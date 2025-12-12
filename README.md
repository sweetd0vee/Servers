# Дашборд нагрузки серверов

### AIOps project

**Запуск в Docker:**


```./docker-build.sh```

```./docker-compose-up.sh```


Файл самой модели имеет большой размер, поэтому мы его в docker-image не заносим, а делаем docker volume и мапим в docker-compose папку с моделью 
/work/models/saiga_yandexgpt_8b.Q8_0.gguf
на папку на локальном компьютере ~/docker-share/models.

**Анализ CPU нагрузки:**
```lambda x: 'Низкая' if x < 20 else ('Высокая' if x > 70 else 'Нормальная')```

**Анализ Memory нагрузки:**
```lambda x: 'Низкая' if x < 30 else ('Высокая' if x > 80 else 'Нормальная')```


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


