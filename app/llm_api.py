from transformers import pipeline, AutoTokenizer
import torch
import platform


def analyze_server_metrics(user_query):
    """
    Анализирует метрики сервера на основе пользовательского запроса
    """

    # Определяем доступное устройство
    if torch.backends.mps.is_available():
        device = "mps"
        torch_dtype = torch.float32  # MPS не поддерживает bfloat16
        print("Используется MPS (Apple Silicon)")
    elif torch.cuda.is_available():
        device = "cuda"
        torch_dtype = torch.bfloat16
        print("Используется CUDA")
    else:
        device = "cpu"
        torch_dtype = torch.float32
        print("Используется CPU")

    # Загружаем токенизатор
    tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-3B-Instruct")

    # Инициализация пайплайна с учетом устройства
    pipe = pipeline(
        "text-generation",
        model="Qwen/Qwen2.5-3B-Instruct",
        tokenizer=tokenizer,
        torch_dtype=torch_dtype,
        device=device if device != "mps" else None,  # Для MPS лучше не указывать device
        device_map="auto" if device != "mps" else None
    )

    # Если MPS, переносим модель вручную
    if device == "mps":
        pipe.model.to("mps")

    # Сообщения для чата
    messages = [
        {
            "role": "system",
            "content": """Ты эксперт по системному администрированию. 
            Анализируй метрики сервера и давай конкретные рекомендации.
            Формат ответа:
            1. Анализ текущего состояния
            2. Выявленные проблемы
            3. Рекомендации по оптимизации
            4. Приоритет действий""",
        },
        {"role": "user", "content": f"Проанализируй метрики сервера: {user_query}"},
    ]

    # Создание промпта
    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    # Параметры генерации
    generation_params = {
        "max_new_tokens": 400,
        "do_sample": True,
        "temperature": 0.7,
        "top_k": 40,
        "top_p": 0.9,
        "repetition_penalty": 1.1,
        "pad_token_id": tokenizer.eos_token_id,
    }

    # Для MPS/CPU добавляем дополнительные параметры
    if device in ["mps", "cpu"]:
        generation_params["temperature"] = 0.3  # Более детерминировано
        generation_params["max_new_tokens"] = 300  # Меньше для скорости

    # Генерация ответа
    outputs = pipe(prompt, **generation_params)

    # Извлекаем только ответ модели
    full_response = outputs[0]["generated_text"]
    if prompt in full_response:
        response = full_response[len(prompt):].strip()
    else:
        response = full_response

    return response


# Альтернатива: использовать float32 вместо bfloat16
def analyze_server_metrics_simple(user_query):
    """
    Упрощенная версия без bfloat16
    """

    # Используем float32 для совместимости
    pipe = pipeline(
        "text-generation",
        model="Qwen/Qwen2.5-3B-Instruct",
        torch_dtype=torch.float32,  # Используем float32 вместо bfloat16
        device_map="auto"
    )

    # Простой промпт без шаблона чата
    prompt = f"""Ты эксперт по анализу метрик сервера. 
Проанализируй следующие метрики и дай рекомендации: {user_query}

Анализ:"""

    outputs = pipe(
        prompt,
        max_new_tokens=300,
        temperature=0.5,
        do_sample=True
    )

    return outputs[0]["generated_text"]


# Версия с CPU-оптимизацией
def analyze_server_metrics_cpu(user_query):
    """
    Оптимизированная версия для CPU
    """
    from transformers import AutoModelForCausalLM

    # Используем int8 для экономии памяти на CPU
    model = AutoModelForCausalLM.from_pretrained(
        "Qwen/Qwen2.5-3B-Instruct",
        load_in_8bit=True,  # Загружаем в 8-битном формате для CPU
        device_map="auto"
    )

    tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-3B-Instruct")

    messages = [
        {"role": "system", "content": "Ты эксперт по системному администрированию."},
        {"role": "user", "content": f"Анализ метрик: {user_query}"}
    ]

    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

    inputs = tokenizer(prompt, return_tensors="pt")

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=200,
            temperature=0.3,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )

    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response


# Пример использования
if __name__ == "__main__":
    # Тестовые запросы
    test_queries = [
        "CPU: 85%, RAM: 70%, Disk: 60%",
        "CPU 95%, память 85%, сеть 75%",
        "Нагрузка: CPU 45%, RAM 50%, 150 запросов/сек"
    ]

    print("Тестирование анализа метрик сервера\n")

    for i, query in enumerate(test_queries, 1):
        print(f"\n{'=' * 60}")
        print(f"Запрос #{i}: {query}")
        print(f"{'=' * 60}")

        try:
            result = analyze_server_metrics(query)
            print("Результат анализа:")
            print(result)
        except Exception as e:
            print(f"Ошибка в основной функции: {e}")
            print("Пробуем упрощенную версию...")
            try:
                result = analyze_server_metrics_simple(query)
                print("Результат (упрощенная версия):")
                print(result)
            except Exception as e2:
                print(f"Ошибка в упрощенной версии: {e2}")
