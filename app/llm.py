import pandas as pd
import streamlit as st
import warnings
import json
import requests
import os
from dotenv import load_dotenv

#LLM_URL = "http://llama-server:8080/completion"
# MAX_TOKENS = 400
# TIMEOUT = 90

def call_ai_analysis(context):
    """Вызов AI для анализа аномалий через Hugging Face"""

    # Используйте переменные окружения
    # api_key = os.getenv("HF_API_KEY")
    api_key=""

    # Если ключ не найден, используем локальный анализ
    if not api_key:
        st.warning("HF_API_KEY не найден. Используется локальный анализ.")
        return local_ai_analysis(context)

    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # Формируем промпт для анализа метрик
        prompt = f"""Ты — опытный SRE-аналитик с 10-летним опытом.
Проанализируй метрики серверов и ответь на вопросы:
1. Есть ли статистические аномалии в данных?
2. Какие серверы требуют внимания и почему?
3. Какие рекомендации можно дать?

Данные метрик:
{json.dumps(context, indent=2, ensure_ascii=False)}

Ответ предоставь в формате:
📊 **Статистический анализ:**
[анализ статистических аномалий]

⚠️ **Проблемные серверы:**
[список проблемных серверов с причинами]

🎯 **Рекомендации:**
[конкретные рекомендации по действиям]

Используй только факты из предоставленных данных."""

        # Выберите одну из доступных моделей Hugging Face:
        # 1. Mixtral (рекомендуется) - бесплатный, мощный
        # 2. Llama 2/3 - также хороший выбор
        # 3. Mistral - легковесный вариант

        model_url = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"

        data = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 1024,  # Максимальное количество токенов в ответе
                "temperature": 0.3,  # Контроль случайности (0-1)
                "top_p": 0.95,  # Ядерная выборка
                "do_sample": True,  # Включить семплирование
                "return_full_text": False,  # Не возвращать промпт в ответе
                "repetition_penalty": 1.1  # Штраф за повторения
            },
            "options": {
                "wait_for_model": True,  # Ждать если модель загружается
                "use_cache": True  # Использовать кеш для ускорения
            }
        }

        # Альтернативная модель (если Mixtral недоступен)
        # model_url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"

        # Для русскоязычных моделей:
        # model_url = "https://api-inference.huggingface.co/models/ai-forever/ruGPT-3.5-13B"

        response = requests.post(
            model_url,
            headers=headers,
            json=data,
            timeout=45  # Увеличиваем таймаут для больших моделей
        )

        if response.status_code == 200:
            result = response.json()

            # Обработка ответа от Hugging Face API
            # Формат ответа может отличаться в зависимости от модели
            if isinstance(result, list) and len(result) > 0:
                if 'generated_text' in result[0]:
                    return result[0]['generated_text']
                elif isinstance(result[0], dict) and len(result[0]) > 0:
                    # Если ответ содержит несколько ключей
                    return str(result[0])
                else:
                    return str(result[0])
            elif isinstance(result, dict):
                if 'generated_text' in result:
                    return result['generated_text']
                else:
                    # Возвращаем весь ответ если формат неизвестен
                    return json.dumps(result, indent=2, ensure_ascii=False)
            else:
                return str(result)

        elif response.status_code == 503:
            # Модель загружается
            st.info("Модель загружается, пожалуйста, подождите 10-20 секунд и попробуйте снова.")
            return local_ai_analysis(context)

        else:
            error_msg = f"Ошибка Hugging Face API: {response.status_code}"
            if response.text:
                try:
                    error_data = response.json()
                    error_msg += f"\nДетали: {error_data.get('error', 'Unknown error')}"
                except:
                    error_msg += f"\nОтвет: {response.text[:200]}"
            st.error(error_msg)
            return local_ai_analysis(context)

    except requests.exceptions.Timeout:
        st.error("Таймаут при обращении к Hugging Face API")
        return local_ai_analysis(context)

    except requests.exceptions.ConnectionError:
        st.error("Ошибка подключения к Hugging Face API")
        return local_ai_analysis(context)

    except Exception as e:
        st.error(f"Непредвиденная ошибка: {str(e)}")
        return local_ai_analysis(context)


def local_ai_analysis(context):
    """Локальный анализ при недоступности API"""
    # Упрощенный локальный анализ
    analysis_result = """📊 **Статистический анализ:**
Проведен базовый анализ метрик. Для детального анализа требуется подключение к AI API.

⚠️ **Проблемные серверы:**
Рекомендуется проверить серверы с пиковыми значениями CPU > 80% и памятью < 20% свободной.

🎯 **Рекомендации:**
1. Настройте автоматическое масштабирование для серверов с высокой нагрузкой
2. Проверьте логи на серверах с аномалиями
3. Рассмотрите возможность оптимизации запросов"""

    return analysis_result