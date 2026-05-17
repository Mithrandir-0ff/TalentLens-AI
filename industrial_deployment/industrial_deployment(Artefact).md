# Артефакт: Промышленная эксплуатация

В рамках задания по промышленной эксплуатации системы TalentLens-AI были выполнены требования по развертыванию и интеграции инструментов наблюдаемости и проксирования моделей.

### 1. Docker Compose для Langfuse и LiteLLM

Предоставлен файл:
docker-compose.yaml и litellm_config.yaml в папке litellm

### 2. Код интеграции системы с Langfuse и LiteLLM

В системе реализована:

#### Интеграция Langfuse

```python
from langfuse.langchain import CallbackHandler

langfuse_handler = CallbackHandler()
Callback добавлен в конфигурацию агента:

```python
config = {
    "configurable": {"thread_id": session_id},
    "callbacks": [
        performance_tracker,
        langfuse_handler
    ]
}

Интеграция LiteLLM
Запросы к модели маршрутизируются через LiteLLM proxy:

TalentLens-AI
→ LiteLLM
→ gpt-oss-120b

Используется virtual key с дневным бюджетом:

$0.01/day

Реализована обработка ошибки превышения бюджета (HTTP 402).

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

### 3. Скриншоты Langfuse
Предоставлены скриншоты:

список трассировок
детализация выполнения запроса
отображение tool calls и token usage
Файл:

industrial_deployment/images/langfuse_traces.png

### 4. Скриншоты LiteLLM
Предоставлены скриншоты:

подключенной модели
страницы virtual keys
управления бюджетами
логов запросов
Файлы:

industrial_deployment/images/litellm_management.png
industrial_deployment/images/litellm_keys.png
industrial_deployment/images/litellm_usage.png