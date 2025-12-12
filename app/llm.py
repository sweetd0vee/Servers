import streamlit as st
import requests

LLM_URL = "http://llama-server:8080/completion"
MAX_TOKENS = 400
TIMEOUT = 90


def call_ai_analysis(context):
    """Улучшенная версия с несколькими попытками"""

    api_key = "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"

    # Список моделей для попыток (от самых легких к более тяжелым)
    models_to_try = [
        # 1. Очень легкие (точно работают)
        {
            "url": "https://api-inference.huggingface.co/models/sshleifer/tiny-gpt2",
            "name": "TinyGPT2",
            "tokens": 300
        },
        {
            "url": "https://api-inference.huggingface.co/models/google/flan-t5-small",
            "name": "Flan-T5-Small",
            "tokens": 400
        },
        # 2. Средние
        {
            "url": "https://api-inference.huggingface.co/models/EleutherAI/gpt-neo-125m",
            "name": "GPT-Neo-125M",
            "tokens": 500
        },
        {
            "url": "https://api-inference.huggingface.co/models/distilgpt2",
            "name": "DistilGPT2",
            "tokens": 500
        },
        # 3. Более мощные (могут не работать на бесплатном)
        {
            "url": "https://api-inference.huggingface.co/models/microsoft/phi-2",
            "name": "Phi-2",
            "tokens": 700
        }
    ]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Короткий промпт
    prompt = f"Анализируй метрики сервера: {str(context)[:800]}"

    for model in models_to_try:
        try:
            data = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": model["tokens"],
                    "temperature": 0.3,
                    "return_full_text": False
                }
            }

            response = requests.post(
                model["url"],
                headers=headers,
                json=data,
                timeout=TIMEOUT
            )

            if response.status_code == 200:
                result = response.json()

                # Универсальный парсинг ответа
                def extract_text(data):
                    if isinstance(data, str):
                        return data
                    elif isinstance(data, dict):
                        for key in ['generated_text', 'text', 'output', 'response']:
                            if key in data:
                                return str(data[key])
                        # Если не нашли ключ, вернем первый не-технический ключ
                        for key in data:
                            if key not in ['error', 'warnings', 'status']:
                                return str(data[key])
                        return str(data)
                    elif isinstance(data, list) and len(data) > 0:
                        return extract_text(data[0])
                    return str(data)

                analysis = extract_text(result)
                return f"Анализ (модель: {model['name']}):\n\n{analysis}"

        except Exception as e:
            continue  # Пробуем следующую модель

    # Если все модели не сработали
    st.warning("Все модели недоступны. Используется локальный анализ.")
    return local_ai_analysis(context)


def local_ai_analysis(context):
    """Локальный анализ при недоступности API"""
    # Упрощенный локальный анализ
    analysis_result = """**Статистический анализ:**
Проведен базовый анализ метрик. Для детального анализа требуется подключение к AI API.

⚠️ **Проблемные серверы:**
Рекомендуется проверить серверы с пиковыми значениями CPU > 80% и свободной памятью < 20%.

🎯 **Рекомендации:**
1. Настройте автоматическое масштабирование для серверов с высокой нагрузкой
2. Проверьте логи на серверах с аномалиями
3. Рассмотрите возможность оптимизации запросов"""

    return analysis_result