from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import os
import json
import uuid
from dotenv import load_dotenv
import uvicorn
from main import agent, structured_llm, PlayerReport, ScoutProjectReport

load_dotenv()

app = FastAPI(title="Talents-AI API")

class ScoutRequest(BaseModel):
    """Запрос пользователя"""
    user_query: str




@app.post("/analyze-player", response_model=ScoutProjectReport)
async def analyze(request: ScoutRequest):
    try:
        session_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": session_id}}
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
                raise ValueError("JSON валиден, но структура не подходит под PlayerReport или ScoutProjectReport")

        except Exception as json_err:
            print(f"Прямой парсинг не удался ({json_err}), пробуем через structured_llm...")
            
            validated_report = structured_llm.invoke(raw_agent_text)
            
            if not validated_report.user_request_context:
                validated_report.user_request_context = request.user_query
                
            return validated_report

    except Exception as e:
        print(f"Критическая ошибка в analyze: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)



