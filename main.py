
import os
import json
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from langchain.agents import create_agent
from api_client import get_player_id, get_player_stats, get_full_player_scout_data, search_team_id, get_team_player_stats, search_tournament_id, get_tournament_seasons
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.callbacks import BaseCallbackHandler
from pydantic import BaseModel, Field, AliasChoices
from langchain.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from knowledge_base import fetch_scouting
load_dotenv()
checkpointer = InMemorySaver()

class PlayerReasoning(BaseModel):
    needed_stats: str = Field(
        description="Извлеки из API конкретные статистические цифры, учитывая позицию игрока и запрос пользователя. Пиши только факты. Формируй мысль коротко, не более 3 предложений."
    )
    stats_comparison: str = Field(
        description="Сравни полученные данные с средними цифрами по лиге/турниру. Используй термины 'выше/лучше/эффективнее' или 'ниже/хуже/менее эффективно' для вердикта. Формируй мысль коротко, не более 3 предложений." 
    )
    tactical_fit: str = Field(
        description="Объясни как выделенная статистика и приведенный анализ закрывает запрос пользователя. Формируй мысль коротко, не более 3 предложений."
    )
    is_valid: bool = Field(
        description="Итоговое решение. True если tats_comparison и tactical_fit валидные."
    )
class ProjectReasoning(BaseModel):
    requirements_check: str = Field(
        description="Краткое подтверждения соответствия найденных кандидатов исходному запросу. Формируй мысль коротко, не более 3 предложений."
    )
    comparative_analysis: str = Field(
        description="Прямое сравнение ключевых метрик кандидатов относительно позиции или запроса пользователя. Формируй мысль коротко, не более 3 предложений."
    )
    selection_justification: str = Field(
        description="Аргументация выбора победителя. Почему Кандидат А лучше Кандидата Б в данном контексте? Формируй мысль коротко, не более 3 предложений."
    )

class MatchDetail(BaseModel):
    date: str = Field(
        validation_alias=AliasChoices('date', 'timestamp', 'startTimestamp'), 
        description="Дата матча (например, 2026-03-28)"
    )
    rating: float = Field(description="Оценка игрока за матч")
    tournament: Optional[str] = Field(default="Unknown Tournament", description="Название турнира")
class PlayerReport(BaseModel):
    reasoning: PlayerReasoning = Field(
        description="Внутренний процесс анализа игрока перед заполнением отчета."
    )
    player_id: int = Field(description="ID игрока из системы")
    name: str = Field(description="Полное имя игрока")

    age: Optional[int] = Field(default=None, description="Возраст игрока")
    market_value: Optional[int] = Field(default=None, description="Стоимость игрока на рынке")
    position_detailed: Optional[str] = Field(default=None, description="Позиция/позиции игрока на поле")
    
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
    project_reasoning: ProjectReasoning = Field(
        description="Пошаговый процесс выбора лучшего кандидата из списка."
    )
    candidates: List[PlayerReport] = Field(description="Список найденных и проанализированных игроков")
    final_recommendation: str = Field(description="Итоговый совет: кого из списка выбрать и почему")

class PlayerIdTool(BaseModel):
    name: str = Field(description="Имя футболиста для поиска на английском языке")
class PlayerStatsInput(BaseModel):
    player_id: int = Field(
        description="Уникальный числовой ID футболиста, полученный из get_player_id_tool"
    )

class FullScoutData(BaseModel):
    player_id: int = Field(description="Уникальный ID игрока")
    season_year: str = Field(
        default="25/26", 
        description="Сезон в формате YY/YY. По умолчанию 25/26"
    )

class TeamIDTool(BaseModel):
    query: str = Field(description="Название футбольного клуба для поиска его ID.")

class TeamPlayerStatsTool(BaseModel):
    team_id: int = Field(
        description="Уникальный числовой ID команды"
    )
    tournament_id: Optional[int] = Field(None,
        description="ID турнира."
    )
    season_id: int = Field(
        description="ID сезона."
    )

class TournamentSearchInput(BaseModel):
    query: str = Field(
        description="Название лиги или турнира на английском (например, 'Bundesliga', 'Premier League', 'Champions League')."
    )

class SeasonsInput(BaseModel):
    tournament_id: int = Field(
        description="ID турнира (uniqueTournament ID), полученный из search_tournament_id_tool."
    )

@tool(args_schema=PlayerIdTool)
def get_player_id_tool(name: str):
    """
    Находит уникальный числовой ID футболиста по его имени. 
    Используй это ВСЕГДА первым шагом, если у тебя нет ID игрока.
    """
    return get_player_id(name)

@tool(args_schema=PlayerStatsInput)
def get_player_stats_tool(player_id: int):
    """
    Получает подробную футбольную статистику и историю матчей по ID игрока.
    Вызывай это только после того, как получишь ID.
    """
    return get_player_stats(player_id)

@tool(args_schema=FullScoutData)
def get_player_full_scout_data_tool(player_id: int, season_year: str = "25/26"):
    """
    Получает ПОЛНУЮ информацию об игроке: возраст, стоимость, позицию И все 
    статистические метрики сезона (голы, xG, ассисты, точность пасов, кроссы, ошибки, блоки, дриблинг).
    Используй это для глубокого анализа соответствия игрока запросу.
    Аргументы:
    - player_id: уникальный ID игрока.
    - season_year: год сезона в формате 'YY/YY' (например, '24/25', '23/24'). 
      ВАЖНО: Если пользователь не указал конкретный сезон в запросе, ВСЕГДА используй значение по умолчанию '25/26'.
    """
    return get_full_player_scout_data(player_id, season_year=season_year)

@tool(args_schema=TeamIDTool)
def search_team_id_tool(query: str):
    """
    Находит уникальный числовой ID футбольной команды по её названию (например, 'Barcelona', 'Real Madrid').
    Используй это ВСЕГДА первым шагом, если пользователь просит найти игроков внутри конкретного клуба.
    """
    return search_team_id(query)

@tool(args_schema=TournamentSearchInput)
def search_tournament_id_tool(query: str):
    """
    Находит ID турнира по его названию. 
    Используй это ПЕРЕД вызовом get_team_player_stats_tool, 
    если не уверен в точном ID лиги.
    """
    return search_tournament_id(query)

@tool(args_schema=SeasonsInput)
def get_tournament_seasons_tool(tournament_id: int):
    """
    Возвращает список сезонов для турнира (например, '24/25', '25/26') и их системные ID.
    Обязательно используй это, чтобы найти актуальный season_id ПЕРЕД вызовом статистики команды.
    """
    return get_tournament_seasons(tournament_id)

@tool(args_schema=TeamPlayerStatsTool)
def get_team_player_stats_tool(team_id: int, tournament_id: int, season_id: int):
    """
    Получает список ВСЕХ игроков команды и их краткую статистику за сезон.
    Используй это, чтобы отфильтровать футболистов по национальности, возрасту, позиции или 
    базовым показателям (голы, рейтинг), прежде чем делать глубокий анализ конкретного игрока.
    """
    return get_team_player_stats(team_id, tournament_id, season_id)


llm = ChatOpenAI(
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-oss-120b",
    base_url="https://litellm.happyhub.ovh/v1",
    temperature=0 
)

structured_llm = llm.with_structured_output(ScoutProjectReport)

system_instruction = f"""
### РОЛЬ
Ты — ведущий элитный AI-скаут системы TalentLens-AI. 
Твоя специализация: анализировать запросы любой сложности — от поиска конкретного игрока до подбора кандидатов по критериям. Ты превращаешь сырые данные API в глубокую спортивную аналитику.

---


### КОНТЕКСТ
Сейчас идет активная фаза трансферного окна. Твои отчеты являются базой для принятия многомиллионных инвестиционных решений. Твой отчет должен учитывать актуальную рыночную стоимость игрока и его готовность к переходу или игре в хорошей команде в целом. Ты работаешь с сырыми данными API в режиме реального времени.

---


### АЛГОРИТМ ОБРАБОТКИ ЗАПРОСА
0. **Методологическая подготовка**: ПРЕЖДЕ ЧЕМ искать статистику, всегда вызывай fetch_scouting. Передай туда название роли или тип анализа из запроса пользователя. Ты ДОЛЖЕН использовать полученные критерии (например, минимальный процент точности паса или количество обводок) для фильтрации кандидатов в финальном отчете.
1. **Поиск по клубу/лиге:** - Если в запросе есть название лиги, ты ОБЯЗАН сначала вызвать `search_tournament_id_tool`. Никогда не угадывай ID турнира.
   - Затем ОБЯЗАТЕЛЬНО вызови `get_tournament_seasons_tool`, чтобы получить актуальный `season_id`. НИКОГДА не передавай просто год (например, 2025 или 2026) в качестве `season_id`.
   - Если нужно найти игрока в конкретном клубе, используй `search_team_id_tool`. 
   - Только имея на руках корректные ID команды, ID турнира И системный `season_id`, переходи к вызову `get_team_player_stats_tool`.
2. **Поиск по характеристикам:** Если пользователь ищет по критериям (например, "правый вингер из Ла Лиги"), и клуб не указан:
   - На основе своих знаний выдели 3-5 наиболее подходящих кандидатов.
   - Для каждого используй `get_player_id_tool`.
3. **Фильтрация и выбор:** Если ты получил список игроков команды через `get_team_player_stats_tool`, отфильтруй их по позиции, возрасту или национальности прямо в уме. Выбери 1-2 самых сильных кандидата, подходящих под запрос.
4. **Глубокий анализ:** Для финального кандидата (или нескольких) ОБЯЗАТЕЛЬНО вызови `get_player_full_scout_data_tool`. Это твой главный источник данных для отчета.
5. **Исключение дублей:** Если ты уже получил данные через `get_player_full_scout_data_tool`, не вызывай `get_player_stats_tool` повторно.
---

### ЦЕЛЬ
Помогать в скаутинге футболистов, предоставляя аналитические отчеты на основе данных из инструментов.

---

### ИНСТРУКЦИИ
1. ПЕРВИЧНЫЙ ПОИСК: Всегда начинай с поиска уникального идентификатора (ID) игрока или команды, используя соответствующие инструменты поиска.
2. СБОР ДАННЫХ: После получения ID используй его для вызова инструментов расширенной статистики или составов команд. Никогда не выдумывай статистику, используй только данные из ответов инструментов.
3. АНАЛИЗ: На основе полученных цифр выдели ключевые показатели, соответствующие запросу пользователя (например, защитные действия, голы или общая форма).
4. ОТЧЕТ: Сформируй краткий структурированный ответ, включающий конкретные цифры и итоговый аналитический вывод.
5. ПРИОРИТЕТ МЕТОДОЛОГИИ: Твои выводы в поле reasoning и recommendation должны базироваться на сравнении реальных цифр из API с нормативами, полученными из fetch_scouting. Если игрок не дотягивает до клубного стандарта, ты обязан указать это в отчете.
6. ПРОВЕРКА КОНТЕКСТА: Если данные из API (например, список игроков команды) кажутся устаревшими или не соответствуют реальности (игрок уже перешел в другой клуб), используй поиск по имени игрока `get_player_id_tool`, чтобы получить его актуальный профиль, прежде чем делать выводы.
7. ЖЕСТКАЯ ПРОВЕРКА КЛУБА: Когда ты получаешь подробные данные через `get_player_full_scout_data_tool`, СТРОГО проверяй поле `club` внутри `profile`. Если текущий клуб игрока в ответе API отличается от клуба, который запросил пользователь (например, игрок уже перешел в другую команду), НЕМЕДЛЕННО исключай его из списка кандидатов.
---

### ФОРМАТ ВЫХОДА
Твой финальный ответ ДОЛЖЕН быть строго в формате JSON, соответствующем схеме ScoutProjectReport.
Сначала заполни внутренние рассуждения (reasoning) для каждого игрока, затем логику сравнения, и только потом давай финальную рекомендацию.

СХЕМА:
{json.dumps(ScoutProjectReport.model_json_schema(), ensure_ascii=False)}
"""



tools = [get_player_id_tool, get_player_stats_tool, get_player_full_scout_data_tool, search_team_id_tool, get_team_player_stats_tool, fetch_scouting, search_tournament_id_tool, get_tournament_seasons_tool]

agent = create_agent(
    model=llm,
    system_prompt=system_instruction,
    tools=tools,
    checkpointer=checkpointer
)

    
import logging
import time
from langchain_core.outputs import LLMResult
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
        self.warning_threshold = warning_threshold
        self.reset()

    def reset(self):
        self.llm_calls = 0
        self.start_time = time.time()
        self.call_start_time = 0
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_tokens = 0

    def on_llm_start(self, serialized, prompts, **kwargs):
        self.llm_calls += 1
        self.call_start_time = time.perf_counter()
        logger.info(f"\n [LLM Call #{self.llm_calls}]")
        logger.info(f"Отправка промпта...")
    
    def on_llm_end(self, response: LLMResult, **kwargs):
        latency = time.perf_counter() - self.call_start_time
        usage = response.llm_output.get("token_usage", {}) if response.llm_output else {}
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", 0)
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.total_tokens += total_tokens
        logger.info(f"Latency: {latency:.2f} sec")
        logger.info(f"Tokens: In: {prompt_tokens} | Out: {completion_tokens} | Total: {total_tokens}")


    def on_tool_start(self, serialized, input_str, **kwargs):
        logger.info(f"[Tool] Агент решил вызвать инструмент. Вход: {input_str}")

    def on_tool_end(self, output: str, **kwargs):
        
        logger.info("-" * 30)
        logger.info(f"[Tool Output] Инструмент вернул данные:")
        logger.info(output) 
        logger.info("-" * 30)
    def get_metrics(self):
        return {
            "llm_calls": self.llm_calls,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_tokens,
            "elapsed_time": time.time() - self.start_time
        }


performance_tracker = ScoutPerformanceTracker()

