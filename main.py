
import os
import json
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from langchain.agents import create_agent
from api_client import get_player_id, get_player_stats, get_full_player_scout_data, search_team_id, get_team_player_stats
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.callbacks import BaseCallbackHandler
from pydantic import BaseModel, Field, AliasChoices
from langchain.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
load_dotenv()
checkpointer = InMemorySaver()

class MatchDetail(BaseModel):
    date: str = Field(
        validation_alias=AliasChoices('date', 'timestamp', 'startTimestamp'), 
        description="Дата матча (например, 2026-03-28)"
    )
    rating: float = Field(description="Оценка игрока за матч")
    tournament: Optional[str] = Field(default="Unknown Tournament", description="Название турнира")
class PlayerReport(BaseModel):
    player_id: int = Field(description="ID игрока из системы")
    name: str = Field(description="Полное имя игрока")
    age: Optional[int] = Field(default=None, description="Возраст игрока")
    market_value: Optional[int] = Field(default=None, description="Стоимость игрока на рынке")
    position_detailed: Optional[str] = Field(default="N/A", description="Позиция/позиции игрока на поле")
    
    season_stats_summary: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Список стат по турнирам"
    )
    
    recent_form_avg: Optional[float] = Field(default=0.0, description="Средняя оценка")
    key_matches: List[MatchDetail] = Field(default_factory=list, description="Список матчей")
    
    verdict: str = Field(default="Данные анализируются", description="Краткий вердикт")
    pro_cons: Optional[str] = Field(default=None, description="Плюсы и минусы")
    recommendation: str = Field(description="Полный текстовый отчет")
class ScoutProjectReport(BaseModel):
    user_request_context: str = Field(description="Краткое описание задачи пользователя")
    candidates: List[PlayerReport] = Field(description="Список найденных и проанализированных игроков")
    final_recommendation: str = Field(description="Итоговый совет: кого из списка выбрать и почему")

@tool
def get_player_id_tool(name: str):
    """
    Находит уникальный числовой ID футболиста по его имени. 
    Используй это ВСЕГДА первым шагом, если у тебя нет ID игрока.
    """
    return get_player_id(name)

@tool
def get_player_stats_tool(player_id: int):
    """
    Получает подробную футбольную статистику и историю матчей по ID игрока.
    Вызывай это только после того, как получишь ID.
    """
    return get_player_stats(player_id)

@tool
def get_player_full_scout_data_tool(player_id: int):
    """
    Получает ПОЛНУЮ информацию об игроке: возраст, стоимость, позицию И все 
    статистические метрики сезона (голы, xG, ассисты, точность пасов, кроссы, ошибки, блоки, дриблинг).
    Используй это для глубокого анализа соответствия игрока запросу.
    """
    return get_full_player_scout_data(player_id)

@tool
def search_team_id_tool(query: str):
    """
    Находит уникальный числовой ID футбольной команды по её названию (например, 'Barcelona', 'Real Madrid').
    Используй это ВСЕГДА первым шагом, если пользователь просит найти игроков внутри конкретного клуба.
    """
    return search_team_id(query)

@tool
def get_team_player_stats_tool(team_id: int, tournament_id: int = 8, season_id: int = 61643):
    """
    Получает список ВСЕХ игроков команды и их краткую статистику за сезон.
    Используй это, чтобы отфильтровать футболистов по национальности, возрасту, позиции или 
    базовым показателям (голы, рейтинг), прежде чем делать глубокий анализ конкретного игрока.
    По умолчанию: Ла Лига (8), Сезон 24/25 (61643).
    """
    return get_team_player_stats(team_id, tournament_id, season_id)



llm = ChatOpenAI(
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-oss-120b",
    base_url="https://litellm.happyhub.ovh/v1",
    temperature=0 
)

structured_llm = llm.with_structured_output(PlayerReport)

system_instruction = f"""
### РОЛЬ
Ты — ведущий элитный AI-скаут системы TalentLens-AI. 
Твоя цель: анализировать запросы любой сложности — от поиска конкретного игрока до подбора кандидатов по критериям. Ты превращаешь сырые данные API в глубокую спортивную аналитику.

### ИНСТРУКЦИЯ ПО РАБОТЕ С ИНСТРУМЕНТАМИ
1. **Поиск по клубу/лиге:** Если пользователь ищет игрока в конкретной команде (например, "найди защитника из Барселоны"), СНАЧАЛА используй `search_team_id_tool`, чтобы получить ID клуба. Затем используй `get_team_player_stats_tool`, чтобы увидеть весь состав и их базовые метрики.
2. **Поиск по характеристикам:** Если пользователь ищет по критериям (например, "правый вингер из Ла Лиги"), и клуб не указан:
   - На основе своих знаний выдели 3-5 наиболее подходящих кандидатов.
   - Для каждого используй `get_player_id_tool`.
3. **Фильтрация и выбор:** Если ты получил список игроков команды через `get_team_player_stats_tool`, отфильтруй их по позиции, возрасту или национальности прямо в уме. Выбери 1-2 самых сильных кандидата, подходящих под запрос.
4. **Глубокий анализ:** Для финального кандидата (или нескольких) ОБЯЗАТЕЛЬНО вызови `get_player_full_scout_data_tool`. Это твой главный источник данных для отчета.
5. **Исключение дублей:** Если ты уже получил данные через `get_player_full_scout_data_tool`, не вызывай `get_player_stats_tool` повторно.

### ЗАДАЧА АНАЛИТИКИ
- **Семантический анализ:** Оцени не только средний балл (recent_form_avg), но и динамику (даты матчей), уровень турниров и стабильность против сильных соперников.
- **Травматичность:** Если в данных есть пропуски между датами матчей, отрази это как возможный риск. Если ты уже получил данные через get_player_full_scout_data_tool, не вызывай get_player_stats_tool повторно, если в этом нет крайней необходимости
- **Вердикт:** Дай четкий ответ — "Рассмотреть для подписания" или "Больше не рассматривать".
- **Рекомендации:** Напиши подробный отчет с заголовками и списками, используя данные о конкретных датах и турнирах.

### ДОП НАСТРОЙКА
Пиши отчет структурировано, используя заголовки и списки.

### ФОРМАТ ВЫХОДА
Твой финальный ответ ДОЛЖЕН быть строго в формате JSON, соответствующем схеме:
{json.dumps(PlayerReport.model_json_schema(), ensure_ascii=False)}
"""



tools = [get_player_id_tool, get_player_stats_tool, get_player_full_scout_data_tool, search_team_id_tool, get_team_player_stats_tool]

agent = create_agent(
    model=llm,
    system_prompt=system_instruction,
    tools=tools,
    checkpointer=checkpointer
)

    
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler("scout_session.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TalentLens-AI")

class ScoutPerformanceTracker(BaseCallbackHandler):
    def __init__(self, warning_threshold: int = 4):
        self.llm_calls = 0
        self.start_time = 0
        self.warning_threshold = warning_threshold

    def on_llm_start(self, serialized, prompts, **kwargs):
        self.llm_calls += 1
        logger.info(f"[Запрос #{self.llm_calls}] Отправка промпта в OpenRouter...")

    def on_tool_start(self, serialized, input_str, **kwargs):
        logger.info(f"[Tool] Агент решил вызвать инструмент. Вход: {input_str}")

    def reset(self):
        self.llm_calls = 0
        self.start_time = time.time()

