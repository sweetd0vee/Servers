# Дашборд нагрузки серверов

## AIOps project

### Executive Summary

This is an AIOps (Artificial Intelligence for IT Operations) dashboard application built with Streamlit for monitoring server
metrics (CPU, Memory, Disk, Network) with AI-powered analysis capabilities. The project uses Docker for containerization,
PostgreSQL for data storage, and integrates with Keycloak for authentication.

**Запуск в Docker:**

Create folder ~/docker-share/models on the local computer with gguf file.

```./docker-build.sh```

```./docker-compose-up.sh```


The model file is too large, so we don't move it to the docker image. We created a docker volume and map a link to the model in docker-compose.

We tested several **LLM models from HuggingFaces**:

- saiga_yandexgpt_8b.Q8_0.gguf (https://huggingface.co/IlyaGusev/saiga_yandexgpt_8b_gguf)
  
- qween2.5-3b-instruct-q6-k.gguf (https://huggingface.co/Qwen/Qwen2.5-3B-Instruct)
  
- zabbix_psql.gguf (https://huggingface.co/Kowshik527/llama_finetuned_zabbix_psql_v1-gguf)


### Purpose
AIOps dashboard for monitoring server metrics (CPU, Memory, Disk, Network) with:
- Real-time visualization (heatmaps, charts, timelines)
- Statistical anomaly detection
- AI-powered analysis using LLM (Qwen2.5-3B-Instruct)
- Role-based access control (Admin, User, Viewer)
- Docker containerization


### Technology Stack
- **Frontend:** Streamlit
- **Backend:** Python 3.12
- **Database:** PostgreSQL (SQLAlchemy ORM)
- **Visualization:** Plotly
- **AI/ML:** Transformers (Hugging Face), llama.cpp
- **Containerization:** Docker Compose
- **Web Server:** Apache HTTPD (reverse proxy)


**Анализ CPU нагрузки:**
```lambda x: 'Низкая' if x < 20 else ('Высокая' if x > 70 else 'Нормальная')```

**Анализ Memory нагрузки:**
```lambda x: 'Низкая' if x < 30 else ('Высокая' if x > 80 else 'Нормальная')```
