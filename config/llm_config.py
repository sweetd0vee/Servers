# Список моделей Hugging Face для попыток (от легких к тяжелым)
HF_MODELS = [
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
    {
        "url": "https://api-inference.huggingface.co/models/microsoft/phi-2",
        "name": "Phi-2",
        "tokens": 700
    }
]

# Конфигурация по умолчанию
DEFAULT_MODEL_NAME = "Qwen/Qwen2.5-3B-Instruct"
DEFAULT_TIMEOUT = 90
DEFAULT_MAX_TOKENS = 400

