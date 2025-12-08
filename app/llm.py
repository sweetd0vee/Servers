import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html, Input, Output, State, dash_table
import glob
import os
import requests
import json
from datetime import datetime

# ================== CONFIG ==================
DATA_DIR = os.getenv("DASH_DATA_DIR", "/app/data")
LLM_URL = "http://llama-server:8080/completion"
MAX_TOKENS = 400
TIMEOUT = 90

# ================== DATA LOADER ==================
def load_all_data():
    files = glob.glob(os.path.join(DATA_DIR, "*.xlsx"))
    dfs = []
    for f in files:
        try:
            df = pd.read_excel(f)
            if 'vm' in df.columns and 'metric' in df.columns:
                df['server'] = df['vm'].str.replace('metrics_', '', regex=False)
                df = df[['date', 'server', 'metric', 'min_value', 'max_value', 'avg_value']].copy()
                dfs.append(df)
        except Exception as e:
            print(f" Ошибка загрузки {f}: {e}")
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    else:
        print(" Нет данных — использую демо-данные")
        return pd.DataFrame({
            'date': [datetime(2025, 12, 1)],
            'server': ['demo-server'],
            'metric': ['cpu.usagemhz.average'],
            'min_value': [70.0],
            'max_value': [75.0],
            'avg_value': [72.7]
        })

# ================== DASH APP ==================
app = dash.Dash(__name__, external_stylesheets=["https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css"])

app.layout = html.Div([
    html.H2("📊 Дашборд нагрузки на виртуальные сервера (CTO View)", className="text-center mt-3"),

    html.Div([
        html.Button("🔄 Обновить данные", id="refresh-btn", className="btn btn-primary me-2"),
        html.Button("🔍 Найти аномалии", id="anomaly-btn", className="btn btn-warning me-2"),
        html.A("📥 Скачать CSV", id="download-link", href="/download", className="btn btn-outline-secondary")
    ], className="text-center mb-3"),

    html.Div([
        html.H4("🤖 Задайте вопрос по метрикам", className="mt-4"),
        dcc.Input(
            id="chat-input",
            placeholder="Например: «Есть ли аномалии у dwh1-nfs?»",
            style={"width": "100%", "padding": "10px", "margin-top": "10px"}
        ),
        html.Div(id="llm-output", className="alert alert-light mt-2", style={"white-space": "pre-wrap"}),
    ], className="container mt-4"),

    html.Div([
        dcc.Dropdown(id="server-filter", placeholder="Выберите сервер", multi=True),
        dcc.Dropdown(id="metric-filter", placeholder="Выберите метрику", multi=True),
        dcc.DatePickerRange(id="date-range", start_date=None, end_date=None)
    ], className="row mb-3"),

    dcc.Graph(id="main-graph"),
    dash_table.DataTable(
        id="data-table",
        page_size=15,
        style_table={"overflowX": "auto"},
        sort_action="native"
    ),
    dcc.Interval(id="auto-refresh", interval=30*1000, n_intervals=0)
])

# ================== LLM ANALYSIS ==================
def analyze_with_llm(df, user_question=None, anomaly_mode=False):
    try:
        df_sample = df.tail(150).copy()
        df_sample['date'] = df_sample['date'].astype(str)
        context = df_sample.to_dict(orient='records')

        if anomaly_mode:
            prompt = f"""Ты — SRE-аналитик. Ниже метрики за последние сутки.

Данные:
{json.dumps(context, indent=2, ensure_ascii=False)}

Инструкции:
- Найди аномалии: метрики, где max_value > avg_value * 1.8
- Назови серверы и метрики
- Дай 2 рекомендации
- Отвечай кратко на русском."""
        else:
            prompt = f"""Ты — SRE-аналитик. Ниже метрики виртуальных серверов.

Данные (пример):
{json.dumps(context, indent=2, ensure_ascii=False)}

Инструкции:
- Отвечай ТОЛЬКО на русском.
- Не придумывай данные — только из контекста.
- Кратко и по делу.

Вопрос пользователя:
«{user_question}»

Ответ:"""

        response = requests.post(
            LLM_URL,
            json={
                "prompt": prompt,
                "temperature": 0.1,
                "n_predict": MAX_TOKENS,
                "stop": ["\n\n", "Вопрос пользователя:"]
            },
            timeout=TIMEOUT
        )
        if response.ok:
            return response.json().get("content", "Ошибка генерации")
        else:
            return f"❌ Ошибка LLM: {response.status_code}"
    except Exception as e:
        return f"⚠️ Нет подключения к LLM: {str(e)}"
