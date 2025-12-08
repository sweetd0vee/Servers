import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from datetime import datetime

# Methods:
# create_cpu_heatmap, create_memory_heatmap
# create_cpu_load_chart, create_mem_load_chart


# Настройка страницы
st.set_page_config(
    page_title="Дашборд мониторинга серверов",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS для светлой темы
st.markdown("""
<style>
    .stApp {
        background-color: #ffffff;
    }
    .main-header {
        font-size: 2.5rem;
        color: #2c3e50;
        text-align: center;
        padding: 20px 0;
        font-weight: 700;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 12px;
        border-left: 5px solid #3498db;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        color: #2c3e50;
    }
    .warning-card {
        background-color: #fff9e6;
        border-left: 5px solid #f39c12;
        padding: 20px;
        border-radius: 12px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        color: #2c3e50;
    }
    .success-card {
        background-color: #e8f6f3;
        border-left: 5px solid #27ae60;
        padding: 20px;
        border-radius: 12px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        color: #2c3e50;
    }
    .danger-card {
        background-color: #fdedec;
        border-left: 5px solid #e74c3c;
        padding: 20px;
        border-radius: 12px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        color: #2c3e50;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #2c3e50 !important;
    }
    .stSidebar {
        background-color: #f8f9fa;
    }
    .css-1d391kg {
        background-color: #ffffff;
    }
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_and_prepare_data():
    """Загрузка и подготовка данных"""
    # Чтение данных из файла
    df = pd.read_excel("data/metrics.xlsx")

    # Преобразование даты
    df['date'] = pd.to_datetime(df['date'])

    # Создание классификации нагрузки
    def classify_load(value, metric_type):
        if metric_type == 'cpu':
            if value < 20:
                return 'Низкая', 'success', '#27ae60'
            elif value < 70:
                return 'Нормальная', 'warning', '#f39c12'
            else:
                return 'Высокая', 'danger', '#e74c3c'
        elif metric_type == 'mem':
            if value < 30:
                return 'Низкая', 'success', '#27ae60'
            elif value < 80:
                return 'Нормальная', 'warning', '#f39c12'
            else:
                return 'Высокая', 'danger', '#e74c3c'
        else:
            return 'Нормальная', 'info', '#3498db'

    # Добавляем классификацию
    for idx, row in df.iterrows():
        if 'cpu.usage' in row['metric']:
            category, _, _ = classify_load(row['avg_value'], 'cpu')
            df.at[idx, 'load_category'] = category
            df.at[idx, 'metric_group'] = 'CPU'
        elif 'mem.usage' in row['metric']:
            category, _, _ = classify_load(row['avg_value'], 'mem')
            df.at[idx, 'load_category'] = category
            df.at[idx, 'metric_group'] = 'Память'
        elif 'disk.usage' in row['metric']:
            df.at[idx, 'load_category'] = 'Нормальная'
            df.at[idx, 'metric_group'] = 'Диск'
        elif 'net.usage' in row['metric']:
            df.at[idx, 'load_category'] = 'Нормальная'
            df.at[idx, 'metric_group'] = 'Сеть'
        else:
            df.at[idx, 'load_category'] = 'Нормальная'
            df.at[idx, 'metric_group'] = 'Другое'

    return df


def create_summary_metrics(df):
    """Создание карточек с метриками"""
    # Общие метрики
    total_servers = df['vm'].nunique()
    start_date = df['date'].min().strftime('%d.%m.%Y')
    end_date = df['date'].max().strftime('%d.%m.%Y')

    # Анализ CPU нагрузки
    cpu_data = df[df['metric'] == 'cpu.usage.average'].copy()
    cpu_data['cpu_category'] = cpu_data['avg_value'].apply(
        lambda x: 'Низкая' if x < 20 else ('Высокая' if x > 70 else 'Нормальная')
    )

    # Анализ Memory нагрузки
    mem_data = df[df['metric'] == 'mem.usage.average'].copy()
    mem_data['mem_category'] = mem_data['avg_value'].apply(
        lambda x: 'Низкая' if x < 30 else ('Высокая' if x > 80 else 'Нормальная')
    )

    # Подсчет по категориям
    cpu_low = cpu_data[cpu_data['cpu_category'] == 'Низкая']['vm'].nunique()
    cpu_normal = cpu_data[cpu_data['cpu_category'] == 'Нормальная']['vm'].nunique()
    cpu_high = cpu_data[cpu_data['cpu_category'] == 'Высокая']['vm'].nunique()

    return {
        'total_servers': total_servers,
        'period': f"{start_date} - {end_date}",
        'cpu_low': cpu_low,
        'cpu_normal': cpu_normal,
        'cpu_high': cpu_high,
        'mem_low': mem_data[mem_data['mem_category'] == 'Низкая']['vm'].nunique(),
        'mem_normal': mem_data[mem_data['mem_category'] == 'Нормальная']['vm'].nunique(),
        'mem_high': mem_data[mem_data['mem_category'] == 'Высокая']['vm'].nunique()
    }


def create_cpu_heatmap(df):
    """Тепловая карта использования CPU по дням"""
    usage_data = df[df['metric'] == 'cpu.usage.average']

    pivot_data = usage_data.pivot_table(
        values='avg_value',
        index='vm',
        columns='date',
        aggfunc='mean'
    )

    # Сортируем по максимальному использованию
    pivot_data['max_usage'] = pivot_data.max(axis=1)
    pivot_data = pivot_data.sort_values('max_usage', ascending=False)
    pivot_data = pivot_data.drop('max_usage', axis=1)

    # Цветовая схема для светлой темы
    fig = px.imshow(
        pivot_data,
        labels=dict(x="Дата", y="Сервер", color="Использование CPU (%)"),
        title="Тепловая карта использования CPU",
        color_continuous_scale=[
            [0, "#e8f6f3"],  # Low - светлый зеленый
            [0.2, "#abebc6"],  # Medium low - зеленый
            [0.4, "#82e0aa"],  #
            [0.6, "#f9e79f"],  # Medium - желтый
            [0.8, "#f8c471"],  # High - оранжевый
            [1.0, "#e74c3c"]  # Critical - красный
        ],
        aspect="auto",
        text_auto='.0f'
    )

    fig.update_layout(
        height=700,
        xaxis_title="Дата",
        yaxis_title="Сервер",
        coloraxis_colorbar=dict(
            title="%",
            thickness=20,
            len=0.8
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#2c3e50')
    )

    return fig


def create_memory_heatmap(df):
    """Тепловая карта использования памяти по дням"""
    usage_data = df[df['metric'] == 'mem.usage.average']

    pivot_data = usage_data.pivot_table(
        values='avg_value',
        index='vm',
        columns='date',
        aggfunc='mean'
    )

    # Сортируем по максимальному использованию
    pivot_data['max_usage'] = pivot_data.max(axis=1)
    pivot_data = pivot_data.sort_values('max_usage', ascending=False)
    pivot_data = pivot_data.drop('max_usage', axis=1)

    fig = px.imshow(
        pivot_data,
        labels=dict(x="Дата", y="Сервер", color="Использование памяти (%)"),
        title="Тепловая карта использования памяти",
        color_continuous_scale=[
            [0, "#e8f6f3"],  # Low - светлый зеленый
            [0.2, "#abebc6"],  # Medium low - зеленый
            [0.4, "#82e0aa"],  #
            [0.6, "#f9e79f"],  # Medium - желтый
            [0.8, "#f8c471"],  # High - оранжевый
            [1.0, "#e74c3c"]  # Critical - красный
        ],
        aspect="auto",
        text_auto='.0f'
    )

    fig.update_layout(
        height=700,
        xaxis_title="Дата",
        yaxis_title="Сервер",
        coloraxis_colorbar=dict(
            title="%",
            thickness=20,
            len=0.8
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#2c3e50')
    )

    return fig


def create_cpu_load_chart(df):
    """Создание графика использования CPU"""
    cpu_data = df[df['metric'] == 'cpu.usage.average']

    # Группируем по серверам
    avg_cpu = cpu_data.groupby('vm')['avg_value'].mean().sort_values(ascending=False).reset_index()

    fig = px.bar(
        avg_cpu,
        x='vm',
        y='avg_value',
        title="Среднее использование CPU по серверам",
        labels={'vm': 'Сервер', 'avg_value': 'Использование CPU (%)'},
        color='avg_value',
        color_continuous_scale=[
            [0, "#e8f6f3"],  # Low - светлый зеленый
            [0.3, "#82e0aa"],  # Medium low - зеленый
            [0.6, "#f9e79f"],  # Medium - желтый
            [0.8, "#f8c471"],  # High - оранжевый
            [1.0, "#e74c3c"]  # Critical - красный
        ]
    )

    fig.update_layout(
        xaxis_tickangle=-45,
        height=500,
        xaxis_title="Сервер",
        yaxis_title="Использование CPU (%)",
        coloraxis_colorbar=dict(title="%"),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#2c3e50')
    )

    # Добавляем горизонтальную линию порога
    fig.add_hline(y=80, line_dash="dash", line_color="red", annotation_text="Критический порог 80%",
                  annotation_font_color="red")
    fig.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Порог низкой нагрузки 30%",
                  annotation_font_color="green")

    return fig


def create_memory_load_chart(df):
    """Создание графика использования памяти"""
    mem_data = df[df['metric'] == 'mem.usage.average']

    # Группируем по серверам
    avg_memory = mem_data.groupby('vm')['avg_value'].mean().sort_values(ascending=False).reset_index()

    fig = px.bar(
        avg_memory,
        x='vm',
        y='avg_value',
        title="Среднее использование памяти по серверам",
        labels={'vm': 'Сервер', 'avg_value': 'Использование памяти (%)'},
        color='avg_value',
        color_continuous_scale=[
            [0, "#e8f6f3"],  # Low - светлый зеленый
            [0.3, "#82e0aa"],  # Medium low - зеленый
            [0.6, "#f9e79f"],  # Medium - желтый
            [0.8, "#f8c471"],  # High - оранжевый
            [1.0, "#e74c3c"]  # Critical - красный
        ]
    )

    fig.update_layout(
        xaxis_tickangle=-45,
        height=500,
        xaxis_title="Сервер",
        yaxis_title="Использование памяти (%)",
        coloraxis_colorbar=dict(title="%"),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#2c3e50')
    )

    # Добавляем горизонтальную линию порога
    fig.add_hline(y=80, line_dash="dash", line_color="red", annotation_text="Критический порог 80%",
                  annotation_font_color="red")
    fig.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Порог низкой нагрузки 30%",
                  annotation_font_color="green")

    return fig


def create_load_timeline(df, selected_server):
    """Создание таймлайна нагрузки для выбранного сервера"""
    server_data = df[df['vm'] == selected_server]

    # CPU данные
    cpu_data = server_data[server_data['metric'] == 'cpu.usage.average']

    # Memory данные
    mem_data = server_data[server_data['metric'] == 'mem.usage.average']

    # Disk данные (если есть)
    disk_data = server_data[server_data['metric'] == 'disk.usage.average']

    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=('CPU Нагрузка', 'Использование памяти', 'Использование диска'),
        vertical_spacing=0.1,
        shared_xaxes=True
    )

    # CPU график
    fig.add_trace(
        go.Scatter(x=cpu_data['date'], y=cpu_data['avg_value'],
                   name='CPU %', mode='lines+markers',
                   line=dict(color='#3498db', width=3),
                   marker=dict(size=6)),
        row=1, col=1
    )

    # Memory график
    fig.add_trace(
        go.Scatter(x=mem_data['date'], y=mem_data['avg_value'],
                   name='Memory %', mode='lines+markers',
                   line=dict(color='#2ecc71', width=3),
                   marker=dict(size=6)),
        row=2, col=1
    )

    # Disk график (если есть данные)
    if not disk_data.empty:
        fig.add_trace(
            go.Scatter(x=disk_data['date'], y=disk_data['avg_value'],
                       name='Disk KB/s', mode='lines+markers',
                       line=dict(color='#e67e22', width=3),
                       marker=dict(size=6)),
            row=3, col=1
        )

    # Пороговые линии
    fig.add_hline(y=70, line_dash="dash", line_color="#e74c3c", row=1, col=1,
                  annotation_text="Высокая нагрузка", annotation_position="top right",
                  annotation_font_color="#e74c3c")
    fig.add_hline(y=80, line_dash="dash", line_color="#e74c3c", row=2, col=1,
                  annotation_text="Критично", annotation_position="top right",
                  annotation_font_color="#e74c3c")

    fig.update_layout(
        height=800,
        showlegend=True,
        title_text=f"Динамика нагрузки сервера: {selected_server}",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#2c3e50'),
        legend=dict(
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='#ddd',
            borderwidth=1
        )
    )

    fig.update_xaxes(
        title_text="Дата",
        row=3, col=1,
        gridcolor='#eee',
        linecolor='#ddd'
    )
    fig.update_yaxes(
        title_text="CPU %",
        row=1, col=1,
        gridcolor='#eee',
        linecolor='#ddd'
    )
    fig.update_yaxes(
        title_text="Memory %",
        row=2, col=1,
        gridcolor='#eee',
        linecolor='#ddd'
    )
    if not disk_data.empty:
        fig.update_yaxes(
            title_text="Disk KB/s",
            row=3, col=1,
            gridcolor='#eee',
            linecolor='#ddd'
        )

    return fig


def create_server_classification_table(df):
    """Создание таблицы классификации серверов"""
    cpu_data = df[df['metric'] == 'cpu.usage.average'].groupby('vm')['avg_value'].mean().reset_index()
    mem_data = df[df['metric'] == 'mem.usage.average'].groupby('vm')['avg_value'].mean().reset_index()

    # Объединяем данные
    classification = pd.merge(cpu_data, mem_data, on='vm', suffixes=('_cpu', '_mem'))

    # Классифицируем
    def classify_cpu(x):
        if x < 20:
            return '🟢 Низкая'
        elif x < 70:
            return '🟡 Нормальная'
        else:
            return '🔴 Высокая'

    def classify_mem(x):
        if x < 30:
            return '🟢 Низкая'
        elif x < 80:
            return '🟡 Нормальная'
        else:
            return '🔴 Высокая'

    def get_recommendation(cpu_cat, mem_cat):
        if '🔴' in cpu_cat or '🔴' in mem_cat:
            return 'Требуется масштабирование'
        elif '🟢' in cpu_cat and '🟢' in mem_cat:
            return 'Возможна консолидация'
        else:
            return 'Нормальная работа'

    classification['CPU Категория'] = classification['avg_value_cpu'].apply(classify_cpu)
    classification['Memory Категория'] = classification['avg_value_mem'].apply(classify_mem)
    classification['Рекомендация'] = classification.apply(
        lambda x: get_recommendation(x['CPU Категория'], x['Memory Категория']), axis=1
    )
    classification['Средний CPU %'] = classification['avg_value_cpu'].round(2)
    classification['Средняя Memory %'] = classification['avg_value_mem'].round(2)

    # Удаляем лишние столбцы
    result = classification[[
        'vm', 'Средний CPU %', 'CPU Категория',
        'Средняя Memory %', 'Memory Категория', 'Рекомендация'
    ]]

    # Переименовываем
    result = result.rename(columns={'vm': 'Сервер'})

    return result


def main():
    # Заголовок
    st.markdown("<h1 class='main-header'>📊 Дашборд мониторинга нагрузки серверов</h1>", unsafe_allow_html=True)

    # Загрузка данных
    with st.spinner('Загрузка и анализ данных...'):
        df = load_and_prepare_data()
        metrics = create_summary_metrics(df)

    # Боковая панель
    with st.sidebar:
        st.markdown("""
        <div style='background-color: #ffffff; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
            <h3 style='color: #2c3e50;'>Фильтры и настройки</h3>
        </div>
        """, unsafe_allow_html=True)

        # Выбор сервера для детального анализа
        servers = sorted(df['vm'].unique())
        selected_server = st.selectbox(
            "Выберите сервер для детального анализа:",
            servers,
            index=0
        )

        # Информация о данных
        st.markdown("---")
        st.markdown(f"""
        <div style='background-color: #f8f9fa; padding: 15px; border-radius: 10px;'>
            <p style='color: #2c3e50;'><strong>Информация о данных:</strong></p>
            <p style='color: #2c3e50;'>📅 Период: {metrics['period']}</p>
            <p style='color: #2c3e50;'>🖥️ Серверов: {metrics['total_servers']}</p>
        </div>
        """, unsafe_allow_html=True)

    # Основной контент
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style='color: #2c3e50;'>Всего серверов</h3>
            <h1 style='color: #3498db; font-size: 3rem;'>{metrics['total_servers']}</h1>
            <p style='color: #7f8c8d;'>Период: {metrics['period']}</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style='color: #2c3e50;'>Нагрузка CPU</h3>
            <p style='color: #27ae60;'>🟢 Низкая: <strong>{metrics['cpu_low']}</strong> серверов</p>
            <p style='color: #f39c12;'>🟡 Нормальная: <strong>{metrics['cpu_normal']}</strong> серверов</p>
            <p style='color: #e74c3c;'>🔴 Высокая: <strong>{metrics['cpu_high']}</strong> серверов</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style='color: #2c3e50;'>Нагрузка памяти</h3>
            <p style='color: #27ae60;'>🟢 Низкая: <strong>{metrics['mem_low']}</strong> серверов</p>
            <p style='color: #f39c12;'>🟡 Нормальная: <strong>{metrics['mem_normal']}</strong> серверов</p>
            <p style='color: #e74c3c;'>🔴 Высокая: <strong>{metrics['mem_high']}</strong> серверов</p>
        </div>
        """, unsafe_allow_html=True)

    # Визуализации
    st.markdown("---")
    st.markdown("<h2 style='color: #2c3e50;'>📈 Визуализация нагрузки</h2>", unsafe_allow_html=True)

    st.subheader("🌡️ Тепловая карта нагрузки CPU")
    fig_heatmap = create_cpu_heatmap(df)
    st.plotly_chart(fig_heatmap, use_container_width=True)

    st.subheader("⚡ Использование CPU")
    fig_chart = create_cpu_load_chart(df)
    st.plotly_chart(fig_chart, use_container_width=True)

    st.subheader("🌡️ Тепловая карта нагрузки по памяти")
    fig_heatmap = create_memory_heatmap(df)
    st.plotly_chart(fig_heatmap, use_container_width=True)

    st.subheader("💾 Использование памяти")
    fig_chart = create_memory_load_chart(df)
    st.plotly_chart(fig_chart, use_container_width=True)

    # Детальный анализ выбранного сервера
    st.markdown("---")
    st.markdown(f"<h2 style='color: #2c3e50;'>🔍 Детальный анализ: {selected_server}</h2>", unsafe_allow_html=True)

    col4, col5 = st.columns(2)

    with col4:
        # Основные метрики сервера
        server_data = df[df['vm'] == selected_server]

        avg_cpu = server_data[server_data['metric'] == 'cpu.usage.average']['avg_value'].mean()
        avg_mem = server_data[server_data['metric'] == 'mem.usage.average']['avg_value'].mean()

        # Определяем статус
        cpu_status = "🟢 Низкая" if avg_cpu < 20 else ("🔴 Высокая" if avg_cpu > 70 else "🟡 Нормальная")
        mem_status = "🟢 Низкая" if avg_mem < 30 else ("🔴 Высокая" if avg_mem > 80 else "🟡 Нормальная")

        st.markdown(f"""
        <div class="metric-card">
            <h3 style='color: #2c3e50;'>📊 Средние значения</h3>
            <p style='color: #2c3e50;'><strong>CPU:</strong> <span style='font-size: 1.2rem; font-weight: bold;'>{avg_cpu:.2f}%</span> - {cpu_status}</p>
            <p style='color: #2c3e50;'><strong>Память:</strong> <span style='font-size: 1.2rem; font-weight: bold;'>{avg_mem:.2f}%</span> - {mem_status}</p>
        </div>
        """, unsafe_allow_html=True)

    with col5:
        # Рекомендации
        if '🔴' in cpu_status:
            recommendation = "⚠️ Требуется немедленное вмешательство - высокая CPU нагрузка!"
            card_class = "danger-card"
        elif '🟢' in cpu_status and '🟢' in mem_status:
            recommendation = "✅ Сервер недогружен - возможна консолидация"
            card_class = "success-card"
        else:
            recommendation = "✅ Сервер работает в нормальном режиме"
            card_class = "success-card"

        st.markdown(f"""
        <div class="{card_class}">
            <h3 style='color: #2c3e50;'>🎯 Рекомендация</h3>
            <p style='color: #2c3e50;'>{recommendation}</p>
        </div>
        """, unsafe_allow_html=True)

    # Таймлайн нагрузки
    st.subheader("📅 Динамика нагрузки во времени")
    fig_timeline = create_load_timeline(df, selected_server)
    st.plotly_chart(fig_timeline, use_container_width=True)

    # Таблица классификации всех серверов
    st.markdown("---")
    st.markdown("<h2 style='color: #2c3e50;'>📋 Классификация всех серверов</h2>", unsafe_allow_html=True)

    classification_table = create_server_classification_table(df)

    # Стилизация таблицы
    st.dataframe(
        classification_table,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Сервер": st.column_config.TextColumn(
                "Сервер",
                help="Название сервера"
            ),
            "Средний CPU %": st.column_config.NumberColumn(
                "CPU %",
                help="Среднее использование CPU",
                format="%.1f%%"
            ),
            "Средняя Memory %": st.column_config.NumberColumn(
                "Memory %",
                help="Среднее использование памяти",
                format="%.1f%%"
            )
        }
    )


if __name__ == "__main__":
    main()