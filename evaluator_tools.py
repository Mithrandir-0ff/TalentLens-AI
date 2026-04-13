import requests
import pandas as pd
import json
import time


API_URL = "http://127.0.0.1:8000/analyze-player"
METRICS_URL = "http://127.0.0.1:8000/metrics"
INPUT_FILE = 'input_prompts_tools.xlsx'
OUTPUT_FILE = 'output_results_tools.xlsx'

def run_evaluation():

    try:
        test_df = pd.read_excel(INPUT_FILE, engine='openpyxl')
    except Exception as e:
        print(f"Ошибка при чтении файла {INPUT_FILE}:")
        print(f"Тип ошибки: {type(e).__name__}")
        print(f"Сообщение: {e}")
        return



    results = []
    total_tests = len(test_df)

    print(f" Запуск системы тестирования. Всего тестов: {total_tests}")

    for index, row in test_df.iterrows():
        test_id = row['id']
        category = row['category']
        user_query = row['query']

        print(f"[{index + 1}/{total_tests}] Тест №{test_id} | {category}")

        start_time = time.time()
        try:
            response = requests.post(API_URL, json={"user_query": user_query}, timeout=300)
            status_code = response.status_code
            latency = round(time.time() - start_time, 2)

            if status_code == 200:
                data = response.json()
                output = json.dumps(data, ensure_ascii=False)

                metrics_response = requests.get(METRICS_URL)
                if metrics_response.status_code == 200:
                    metrics = metrics_response.json()
                    llm_calls = metrics.get('llm_calls', 0)
                    input_tokens = metrics.get('total_prompt_tokens', 0)
                    output_tokens = metrics.get('total_completion_tokens', 0)
                    total_tokens = metrics.get('total_tokens', 0)
                else:
                    llm_calls = 0
                    input_tokens = 0
                    output_tokens = 0
                    total_tokens = 0
            else:
                output = f"Error {status_code}: {response.text}"
                llm_calls = 0
                input_tokens = 0
                output_tokens = 0
                total_tokens = 0
        except Exception as e:
            output = f"Connection Failed: {str(e)}"
            latency = 0
            llm_calls = 0
            input_tokens = 0
            output_tokens = 0
            total_tokens = 0
        
        results.append({
            "id": test_id,
            "Категория": category,
            "Запрос": user_query,
            "Результат": output,
            "Время (сек)": latency,
            "Шагов LLM": llm_calls,
            "Токенов (вход)": input_tokens,
            "Токенов (выход)": output_tokens,
            "Токенов (всего)": total_tokens
        })
    result_df = pd.DataFrame(results)
    result_df.to_excel(OUTPUT_FILE, index=False)
    
    print("-" * 30)
    print(f"Результаты сохранены в: {OUTPUT_FILE}")
    return result_df



if __name__ == "__main__":
    run_evaluation()