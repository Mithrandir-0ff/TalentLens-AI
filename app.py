from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Any, Dict
import os
import json
import uuid
import time
from dotenv import load_dotenv
import uvicorn
from main import agent, structured_llm, PlayerReport, ScoutProjectReport, performance_tracker, langfuse_handler

load_dotenv()

app = FastAPI(title="Talents-AI API")

class ScoutRequest(BaseModel):
    """Запрос пользователя"""
    user_query: str

class MetricsResponse(BaseModel):
    llm_calls: int
    total_prompt_tokens: int
    total_completion_tokens: int
    total_tokens: int
    elapsed_time: float

@app.post("/analyze-player", response_model=ScoutProjectReport)
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

        result = agent.invoke(inputs, config=config)
        raw_agent_text = result["messages"][-1].content
        
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

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)