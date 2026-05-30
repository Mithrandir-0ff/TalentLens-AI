from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Any, Dict, Union
import os
import json
import uuid
from main import OFF_TOPIC_RESPONSE
import time
from dotenv import load_dotenv
import uvicorn
from service import get_service
from api_schema.schemas import RunRequest, RunResponse, InfoResponse
from main import final_graph
from main import agent, structured_llm, PlayerReport, ScoutProjectReport, performance_tracker, langfuse_handler

load_dotenv()

app = FastAPI(title="Talents-AI API")

class ScoutRequest(BaseModel):
    """Запрос пользователя"""
    user_query: str

class OffTopicResponse(BaseModel):
    message: str

class MetricsResponse(BaseModel):
    llm_calls: int
    total_prompt_tokens: int
    total_completion_tokens: int
    total_tokens: int
    elapsed_time: float

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str = "talentlens-ai"
    messages: List[ChatMessage]
    stream: bool = False


def transform_scout_output_to_text(raw_output: Any) -> str:
    if isinstance(raw_output, str):
        try:
            clean_str = raw_output.strip()
            if "```json" in clean_str:
                clean_str = clean_str.split("```json")[1].split("```")[0].strip()
            elif "```" in clean_str:
                clean_str = clean_str.split("```")[1].split("```")[0].strip()
            data = json.loads(clean_str)
        except Exception:
            return raw_output
    elif hasattr(raw_output, 'model_dump'):
        data = raw_output.model_dump()
    if isinstance(data, dict):
        if "candidates" in data or "final_recommendation" in data:
            markdown_text = f"## Скаутский отчет по запросу: *\"{data.get('user_request_context', 'Анализ игроков')}\"*\n\n"
            reasoning = data.get("project_reasoning", {})
            if reasoning:
                markdown_text += "### Аналитическое обоснование:\n"
                markdown_text += f"- **Соответствие требованиям:** {reasoning.get('requirements_check', '')}\n"
                markdown_text += f"- **Сравнение ключевых метрик:** {reasoning.get('comparative_analysis', '')}\n"
                markdown_text += f"- **Аргументация выбора:** {reasoning.get('selection_justification', '')}\n"

            markdown_text += "### Рассмотренные кандидаты:\n"
            for candidate in data.get('candidates', []):
                reason = candidate.get('reasoning', {})
                markdown_text += f"### Имя игрока: {candidate.get('name', 'Неизвестно')} (ID: {candidate.get('player_id', 'Неизвестно')})\n"
                markdown_text += f"- **Возраст:** {candidate.get('age', 'Неизвестно')}\n"
                markdown_text += f"- **Рыночная стоимость:** {candidate.get('market_value', 'Неизвестно')}\n"
                markdown_text += f"- **Детальная позиция:** {candidate.get('position_detailed', 'Неизвестно')}\n"
                markdown_text += f"- **Средняя оценка за последние матчи:** {candidate.get('recent_form_avg', '0.0')}\n"
                markdown_text += "- **Статистика за сезон по турнирам:**\n"
                
                stats_summary = candidate.get('season_stats_summary', [])
                if stats_summary:
                    for tournament_stat in stats_summary:
                        t_name = tournament_stat.get('tournament', 'Unknown Tournament')
                        markdown_text += f"  - *Турнир:* **{t_name}**\n"
                        
                        for metric, value in tournament_stat.items():
                            if metric != 'tournament' and value is not None:
                                markdown_text += f"    - {metric}: `{value}`\n"
                else:
                    markdown_text += "  - Данные о статистике сезона отсутствуют\n"

                if reason:
                    markdown_text += "- **Анализ скаута:**\n"
                    markdown_text += f" - *Необходимые метрики:* {reason.get('needed_stats', 'Нет данных')}\n"
                    markdown_text += f" - *Сравнение по лиге:* {reason.get('stats_comparison', 'Нет данных')}\n"
                    markdown_text += f" - *Тактическое соответствие:* {reason.get('tactical_fit', 'Нет данных')}\n"

                markdown_text += f"- **Плюсы и Минусы:** {candidate.get('pro_cons', 'Нет данных')}\n"
                markdown_text += f"- **Вердикт по игроку:** *{candidate.get('verdict', 'Нет данных')}*\n"
                markdown_text += f"- **Развернутая рекомендация:** {candidate.get('recommendation', 'Нет данных')}\n\n"
                markdown_text += "---\n\n"

            markdown_text += "## - Финальное заключение\n"
            markdown_text += f"**{data.get('final_recommendation', 'Нет данных')}**\n"

            return markdown_text
        return str(raw_output)

@app.post("/analyze-player", response_model=Union[ScoutProjectReport, OffTopicResponse])
async def analyze(request: ScoutRequest):
    performance_tracker.reset()
    raw_agent_text = None
    try:
        session_id = str(uuid.uuid4())
        config = {
            "configurable": {"thread_id": session_id},
            "callbacks": [performance_tracker, langfuse_handler] 
        }
        inputs = {"messages": [("user", request.user_query)]}

        result = final_graph.invoke(inputs, config=config)
        raw_agent_text = result["messages"][-1].content
        
        if raw_agent_text.strip() == OFF_TOPIC_RESPONSE.strip():
            return OffTopicResponse(
                message=OFF_TOPIC_RESPONSE
            )


        print(f"DEBUG: Агент выдал текст: {raw_agent_text}")

        if not raw_agent_text:
            raise HTTPException(status_code=500, detail="Агент вернул пустой ответ")

        try:
            clean_json = raw_agent_text.strip()
            if "```json" in clean_json:
                clean_json = clean_json.split("```json")[1].split("```")[0].strip()
            elif "```" in clean_json:
                clean_json = clean_json.split("```")[1].split("```")[0].strip()

            data_dict = json.loads(clean_json)
            
            if "player_id" in data_dict and "candidates" not in data_dict:
                final_data = {
                    "user_request_context": request.user_query,
                    "candidates": [data_dict],
                    "final_recommendation": data_dict.get("verdict", "Анализ одного игрока завершен.")
                }
                return ScoutProjectReport(**final_data)
            
            elif "candidates" in data_dict:
                if not data_dict.get("user_request_context"):
                    data_dict["user_request_context"] = request.user_query
                return ScoutProjectReport(**data_dict)
            
            else:
                raise ValueError("JSON валиден, но структура не подходит")

        except Exception as json_err:
            print(f"Ошибка парсинга JSON: {json_err}")
            raise HTTPException(status_code=500, detail="Ошибка обработки ответа модели")

    except Exception as e:
        error_text = str(e).lower()

        print(f"Критическая ошибка в analyze: {e}")

        if (
            "402" in error_text
            or "budget" in error_text
            or "payment required" in error_text
            or "exceeded" in error_text
        ):
            raise HTTPException(
                status_code=402,
                detail="Дневной лимит LiteLLM исчерпан"
            )

        if raw_agent_text:
            try:
                validated_report = structured_llm.invoke(raw_agent_text)

                if not validated_report.user_request_context:
                    validated_report.user_request_context = request.user_query

                return validated_report

            except Exception:
                pass

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    
@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    metrics = performance_tracker.get_metrics()
    return MetricsResponse(**metrics)

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    user_message = request.messages[-1].content
    
    session_id = str(uuid.uuid4())
    config = {
        "configurable": {"thread_id": session_id},
        "callbacks": [performance_tracker, langfuse_handler]
    }
    
    inputs = {"messages": [("user", user_message)]}
    result = final_graph.invoke(inputs, config=config)
    raw_text = result["messages"][-1].content
    
    clean_markdown_text = transform_scout_output_to_text(raw_text)

    return {
        "id": f"chatcmpl-{session_id}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": clean_markdown_text
                },
                "finish_reason": "stop"
            }
        ]
    }


@app.get("/v1/models")
async def get_models():
    return {
        "object": "list",
        "data": [
            {
                "id": "talentlens-ai",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "talentlens"
            }
        ]
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/info", response_model=InfoResponse)
async def info():
    return get_service().get_info()


@app.post("/run", response_model=RunResponse)
async def run(request: RunRequest):
    return get_service().run(request)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)