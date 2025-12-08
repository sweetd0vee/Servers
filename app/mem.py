import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from datetime import datetime, timedelta

# Настройка страницы
st.set_page_config(
    page_title="Анализ использования памяти серверов",
    page_icon="💾",
    layout="wide"
)

# Загрузка CSS
st.markdown("""
<style>
    .memory-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 25px;
        border-radius: 10px;
        margin-bottom: 30px;
        text-align: center;
    }
    .memory-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 20px;
        border-radius: 10px;
        margin: 15px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .threshold-line {
        border-left: 3px solid #ff6b6b;
        padding-left: 10px;
        margin: 5px 0;
    }
    .server-tag {
        display: inline-block;
        background-color: #4a6fa5;
        color: white;
        padding: 3px 10px;
        border-radius: 15px;
        margin: 2px;
        font-size: 0.9em;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_memory_data():
    """Загрузка и фильтрация данных по памяти"""
    df = pd.read_excel("data/metrics.xlsx")
    df['date'] = pd.to_datetime(df['date'])

    # Фильтруем только данные по памяти
    memory_metrics = [
        'mem.usage.average',
        'mem.consumed.average',
        'mem.overhead.average',
        'mem.vmmemctl.average',
        'mem.swapinrate.average',
        'mem.swapoutrate.average'
    ]

    memory_df = df[df['metric'].isin(memory_metrics)].copy()

    # Конвертируем consumed memory в GB для лучшей читаемости
    if 'mem.consumed.average' in memory_df['metric'].values:
        consumed_data = memory_df[memory_df['metric'] == 'mem.consumed.average'].copy()
        consumed_data['avg_value'] = consumed_data['avg_value'] / (1024 ** 3)  # Convert to GB
        memory_df = pd.concat([memory_df[memory_df['metric'] != 'mem.consumed.average'], consumed_data])

    return memory_df


def create_memory_summary_cards(memory_df):
    """Создание карточек с общими метриками памяти"""
    usage_data = memory_df[memory_df['metric'] == 'mem.usage.average']

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        avg_usage = usage_data['avg_value'].mean()
        st.metric(
            label="Среднее использование памяти",
            value=f"{avg_usage:.1f}%",
            delta=None
        )

    with col2:
        max_usage = usage_data['avg_value'].max()
        max_server = usage_data.loc[usage_data['avg_value'].idxmax(), 'vm']
        st.metric(
            label="Максимальное использование",
            value=f"{max_usage:.1f}%",
            delta=f"Сервер: {max_server.split('_')[-1]}"
        )

    with col3:
        high_load_count = len(usage_data[usage_data['avg_value'] > 80])
        total_count = len(usage_data)
        st.metric(
            label="Высокая нагрузка (>80%)",
            value=f"{high_load_count}",
            delta=f"из {total_count}"
        )

    with col4:
        low_load_count = len(usage_data[usage_data['avg_value'] < 30])
        st.metric(
            label="Низкая нагрузка (<30%)",
            value=f"{low_load_count}",
            delta=f"из {total_count}"
        )


def create_memory_usage_trend(memory_df, selected_servers=None):
    """График тренда использования памяти"""
    usage_data = memory_df[memory_df['metric'] == 'mem.usage.average']

    if selected_servers:
        usage_data = usage_data[usage_data['vm'].isin(selected_servers)]

    # Выбираем топ-10 серверов по среднему использованию
    top_servers = usage_data.groupby('vm')['avg_value'].mean().nlargest(10).index
    filtered_data = usage_data[usage_data['vm'].isin(top_servers)]

    fig = px.line(
        filtered_data,
        x='date',
        y='avg_value',
        color='vm',
        title="📈 Тренд использования памяти (топ-10 серверов)",
        labels={'avg_value': 'Использование памяти (%)', 'date': 'Дата', 'vm': 'Сервер'},
        line_shape='spline',
        render_mode='svg'
    )

    # Добавляем пороговые линии
    fig.add_hline(y=80, line_dash="dash", line_color="red",
                  annotation_text="Критический порог 80%",
                  annotation_position="top left")
    fig.add_hline(y=30, line_dash="dash", line_color="green",
                  annotation_text="Порог низкой нагрузки 30%")

    fig.update_layout(
        height=500,
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis_title="Дата",
        yaxis_title="Использование памяти (%)",
        plot_bgcolor='rgba(240, 242, 246, 0.8)'
    )

    return fig


def create_memory_heatmap(memory_df):
    """Тепловая карта использования памяти по дням"""
    usage_data = memory_df[memory_df['metric'] == 'mem.usage.average']

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
            [0, "#2E8B57"],  # Low - green
            [0.3, "#90EE90"],  # Medium low - light green
            [0.7, "#FFD700"],  # Medium - yellow
            [0.8, "#FF8C00"],  # High - orange
            [1.0, "#FF4500"]  # Critical - red
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
        )
    )

    return fig


def create_memory_distribution_chart(memory_df):
    """Гистограмма распределения использования памяти"""
    usage_data = memory_df[memory_df['metric'] == 'mem.usage.average']

    # Берем последние данные для каждого сервера
    latest_data = usage_data.sort_values('date').groupby('vm').last().reset_index()

    # Категоризируем
    bins = [0, 30, 60, 80, 100]
    labels = ['Низкая (<30%)', 'Нормальная (30-60%)', 'Высокая (60-80%)', 'Критическая (>80%)']
    colors = ['#2E8B57', '#FFD700', '#FF8C00', '#FF4500']

    latest_data['category'] = pd.cut(latest_data['avg_value'], bins=bins, labels=labels)

    # Подсчет по категориям
    category_counts = latest_data['category'].value_counts().reindex(labels)

    fig = px.bar(
        x=category_counts.index,
        y=category_counts.values,
        title="Распределение серверов по уровню использования памяти",
        labels={'x': 'Категория использования', 'y': 'Количество серверов'},
        color=category_counts.index,
        color_discrete_sequence=colors
    )

    fig.update_layout(
        height=400,
        xaxis_title="Уровень использования памяти",
        yaxis_title="Количество серверов",
        showlegend=False,
        plot_bgcolor='rgba(240, 242, 246, 0.8)'
    )

    # Добавляем аннотации
    for i, value in enumerate(category_counts.values):
        fig.add_annotation(
            x=i,
            y=value + 0.5,
            text=str(value),
            showarrow=False,
            font=dict(size=12, color='black')
        )

    return fig


def create_server_comparison_chart(memory_df, selected_servers):
    """Сравнение нескольких серверов"""
    if not selected_servers:
        selected_servers = memory_df['vm'].unique()[:3]

    usage_data = memory_df[
        (memory_df['metric'] == 'mem.usage.average') &
        (memory_df['vm'].isin(selected_servers))
        ]

    fig = go.Figure()

    colors = px.colors.qualitative.Set3
    for i, server in enumerate(selected_servers):
        server_data = usage_data[usage_data['vm'] == server]

        fig.add_trace(go.Box(
            y=server_data['avg_value'],
            name=server.split('_')[-1],
            boxpoints='all',
            jitter=0.3,
            pointpos=-1.8,
            marker_color=colors[i % len(colors)],
            line_color=colors[i % len(colors)]
        ))

    fig.update_layout(
        title=f"📊 Сравнение использования памяти ({len(selected_servers)} серверов)",
        yaxis_title="Использование памяти (%)",
        xaxis_title="Сервер",
        height=500,
        showlegend=False,
        plot_bgcolor='rgba(240, 242, 246, 0.8)'
    )

    fig.add_hline(y=80, line_dash="dash", line_color="red",
                  annotation_text="Критический порог 80%")

    return fig


def create_detailed_memory_breakdown(memory_df, selected_server):
    """Детальный анализ памяти для выбранного сервера"""
    server_data = memory_df[memory_df['vm'] == selected_server]

    # Получаем разные метрики памяти
    metrics = {
        'mem.usage.average': 'Общее использование',
        'mem.consumed.average': 'Потреблено (GB)',
        'mem.overhead.average': 'Накладные расходы',
        'mem.vmmemctl.average': 'Balloon driver',
        'mem.swapinrate.average': 'Swap-in',
        'mem.swapoutrate.average': 'Swap-out'
    }

    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=[metrics.get(m, m) for m in server_data['metric'].unique()[:6]],
        vertical_spacing=0.1,
        horizontal_spacing=0.1
    )

    for i, (metric, title) in enumerate(metrics.items()):
        if i >= 6:
            break

        metric_data = server_data[server_data['metric'] == metric]

        if not metric_data.empty:
            row = i // 2 + 1
            col = i % 2 + 1

            fig.add_trace(
                go.Scatter(
                    x=metric_data['date'],
                    y=metric_data['avg_value'],
                    mode='lines+markers',
                    name=title,
                    line=dict(width=2)
                ),
                row=row, col=col
            )

    fig.update_layout(
        height=800,
        title_text=f"🔍 Детальный анализ памяти: {selected_server}",
        showlegend=False
    )

    return fig


def create_peak_memory_usage_table(memory_df):
    """Таблица пикового использования памяти"""
    usage_data = memory_df[memory_df['metric'] == 'mem.usage.average']

    peak_usage = usage_data.groupby('vm').agg({
        'avg_value': ['max', 'mean', 'min'],
        'date': lambda x: x.iloc[usage_data.loc[x.index, 'avg_value'].idxmax()].strftime('%Y-%m-%d')
    }).round(2)

    peak_usage.columns = ['Пиковое значение (%)', 'Среднее значение (%)', 'Минимальное значение (%)', 'Дата пика']
    peak_usage = peak_usage.sort_values('Пиковое значение (%)', ascending=False)

    # Добавляем цветовую маркировку
    def color_cells(val):
        if val > 80:
            return 'background-color: #ff6b6b; color: white;'
        elif val > 60:
            return 'background-color: #ffd166;'
        elif val < 30:
            return 'background-color: #06d6a0; color: white;'
        return ''

    styled_table = peak_usage.style.applymap(color_cells, subset=['Пиковое значение (%)', 'Среднее значение (%)'])

    return styled_table


def main():
    # Заголовок
    st.markdown("""
    <div class="memory-header">
        <h1>💾 Анализ использования памяти серверов</h1>
        <p>Период: 2025-11-25 — 2025-12-01 | Всего серверов: 20</p>
    </div>
    """, unsafe_allow_html=True)

    # Загрузка данных
    with st.spinner('Загрузка данных о памяти...'):
        memory_df = load_memory_data()

    # Боковая панель
    with st.sidebar:
        st.header("⚙️ Настройки анализа")

        # Выбор серверов
        all_servers = sorted(memory_df['vm'].unique())
        selected_servers = st.multiselect(
            "Выберите серверы для анализа:",
            all_servers,
            default=all_servers[:5]
        )

        # Выбор сервера для детального анализа
        selected_detailed_server = st.selectbox(
            "Выберите сервер для детального анализа:",
            all_servers,
            index=0
        )

        # Фильтр по датам
        min_date = memory_df['date'].min()
        max_date = memory_df['date'].max()

        date_range = st.date_input(
            "Диапазон дат:",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )

        if len(date_range) == 2:
            start_date, end_date = date_range
            memory_df = memory_df[
                (memory_df['date'] >= pd.Timestamp(start_date)) &
                (memory_df['date'] <= pd.Timestamp(end_date))
                ]

        # Пороговые значения
        st.subheader("📊 Пороговые значения")
        critical_threshold = st.slider("Критический порог (%)", 70, 95, 80)
        warning_threshold = st.slider("Предупреждение (%)", 50, 90, 60)

    # Основные метрики
    create_memory_summary_cards(memory_df)

    # Основные графики
    col1, col2 = st.columns(2)

    with col1:
        st.plotly_chart(
            create_memory_distribution_chart(memory_df),
            use_container_width=True
        )

    with col2:
        if selected_servers:
            st.plotly_chart(
                create_server_comparison_chart(memory_df, selected_servers),
                use_container_width=True
            )

    # Тепловая карта
    st.plotly_chart(
        create_memory_heatmap(memory_df),
        use_container_width=True
    )

    # Тренд использования
    st.plotly_chart(
        create_memory_usage_trend(memory_df, selected_servers),
        use_container_width=True
    )

    # Таблица пикового использования
    st.header("📋 Таблица пикового использования памяти")
    peak_table = create_peak_memory_usage_table(memory_df)
    st.dataframe(
        peak_table,
        use_container_width=True,
        height=600
    )

    # Детальный анализ
    st.header(f"🔍 Детальный анализ: {selected_detailed_server}")
    detailed_fig = create_detailed_memory_breakdown(memory_df, selected_detailed_server)
    st.plotly_chart(detailed_fig, use_container_width=True)

    # Предупреждения
    st.header("⚠️ Серверы требующие внимания")

    usage_data = memory_df[memory_df['metric'] == 'mem.usage.average']
    critical_servers = usage_data.groupby('vm')['avg_value'].max()
    critical_servers = critical_servers[critical_servers > critical_threshold]

    if not critical_servers.empty:
        st.error("**Серверы с критическим использованием памяти (>80%):**")
        for server, usage in critical_servers.items():
            st.markdown(f"""
            <div class="threshold-line">
                <strong>{server.split('_')[-1]}</strong>: {usage:.1f}% памяти
                <span style="color: #ff6b6b; font-size: 0.9em;">(Требуется масштабирование)</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("✅ Нет серверов с критическим использованием памяти")

    # Недогруженные серверы
    underutilized_servers = usage_data.groupby('vm')['avg_value'].mean()
    underutilized_servers = underutilized_servers[underutilized_servers < 30]

    if not underutilized_servers.empty:
        st.info("**Недогруженные серверы (<30% памяти):**")
        servers_html = "".join([f'<span class="server-tag">{s.split("_")[-1]}</span>'
                                for s in underutilized_servers.index])
        st.markdown(servers_html, unsafe_allow_html=True)
        st.caption("Эти серверы могут быть кандидатами для консолидации.")

    # Экспорт данных
    st.markdown("---")
    st.header("📥 Экспорт данных")

    col3, col4 = st.columns(2)

    with col3:
        # Экспорт данных по памяти
        memory_csv = memory_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Скачать все данные о памяти (CSV)",
            data=memory_csv,
            file_name="memory_usage_data.csv",
            mime="text/csv",
            help="Скачать полный набор данных по использованию памяти"
        )

    with col4:
        # Экспорт сводного отчета
        summary_data = usage_data.groupby('vm').agg({
            'avg_value': ['max', 'mean', 'min']
        }).round(2)
        summary_data.columns = ['Максимум (%)', 'Среднее (%)', 'Минимум (%)']
        summary_csv = summary_data.to_csv().encode('utf-8')

        st.download_button(
            label="📥 Скачать сводный отчет (CSV)",
            data=summary_csv,
            file_name="memory_summary.csv",
            mime="text/csv",
            help="Скачать сводную статистику по использованию памяти"
        )


if __name__ == "__main__":
    main()