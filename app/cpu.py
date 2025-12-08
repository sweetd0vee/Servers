import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from datetime import datetime, timedelta

# Настройка страницы
st.set_page_config(
    page_title="Анализ CPU нагрузки серверов",
    page_icon="⚡",
    layout="wide"
)

# Загрузка CSS
st.markdown("""
<style>
    .cpu-header {
        background: linear-gradient(135deg, #ff7e5f 0%, #feb47b 100%);
        color: white;
        padding: 25px;
        border-radius: 10px;
        margin-bottom: 30px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .cpu-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 20px;
        border-radius: 10px;
        margin: 15px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-left: 5px solid #ff7e5f;
    }
    .critical-card {
        background: linear-gradient(135deg, #fff5f5 0%, #ffe5e5 100%);
        border-left: 5px solid #ff6b6b;
        animation: pulse 2s infinite;
    }
    .warning-card {
        background: linear-gradient(135deg, #fff9db 0%, #fff3bf 100%);
        border-left: 5px solid #ffd43b;
    }
    .success-card {
        background: linear-gradient(135deg, #ebfbee 0%, #d3f9d8 100%);
        border-left: 5px solid #51cf66;
    }
    .threshold-line {
        border-left: 3px solid #ff6b6b;
        padding-left: 10px;
        margin: 8px 0;
        background-color: rgba(255, 107, 107, 0.1);
        border-radius: 5px;
    }
    .server-tag {
        display: inline-block;
        background: linear-gradient(135deg, #ff7e5f 0%, #feb47b 100%);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        margin: 3px;
        font-size: 0.9em;
        font-weight: 500;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.8; }
        100% { opacity: 1; }
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_cpu_data():
    """Загрузка и фильтрация данных по CPU"""
    df = pd.read_excel("data/metrics.xlsx")
    df['date'] = pd.to_datetime(df['date'])

    # Фильтруем только данные по CPU
    cpu_metrics = [
        'cpu.usage.average',
        'cpu.usagemhz.average',
        'cpu.ready.summation'
    ]

    cpu_df = df[df['metric'].isin(cpu_metrics)].copy()

    # Добавляем категоризацию нагрузки
    def categorize_cpu_load(value):
        if value < 20:
            return 'Низкая', '#51cf66', '🟢'
        elif value < 70:
            return 'Нормальная', '#ffd43b', '🟡'
        else:
            return 'Высокая', '#ff6b6b', '🔴'

    cpu_usage_data = cpu_df[cpu_df['metric'] == 'cpu.usage.average'].copy()
    cpu_usage_data[['load_category', 'color', 'icon']] = cpu_usage_data['avg_value'].apply(
        lambda x: pd.Series(categorize_cpu_load(x))
    )

    return cpu_df, cpu_usage_data


def create_cpu_summary_cards(cpu_usage_data):
    """Создание карточек с общими метриками CPU"""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        avg_cpu = cpu_usage_data['avg_value'].mean()
        status = "🟡 Нормальная" if avg_cpu < 70 else "🔴 Высокая"
        st.metric(
            label="Средняя CPU нагрузка",
            value=f"{avg_cpu:.1f}%",
            delta=status
        )

    with col2:
        max_cpu = cpu_usage_data['avg_value'].max()
        max_server = cpu_usage_data.loc[cpu_usage_data['avg_value'].idxmax(), 'vm']
        st.metric(
            label="Максимальная нагрузка",
            value=f"{max_cpu:.1f}%",
            delta=f"{max_server.split('_')[-1]}"
        )

    with col3:
        high_load_count = len(cpu_usage_data[cpu_usage_data['avg_value'] > 70])
        total_count = cpu_usage_data['vm'].nunique()
        st.metric(
            label="Высокая нагрузка (>70%)",
            value=f"{high_load_count}",
            delta=f"из {total_count} серверов",
            delta_color="inverse"
        )

    with col4:
        # CPU Ready - показатель задержки
        if 'cpu.ready.summation' in cpu_usage_data['metric'].unique():
            ready_data = cpu_usage_data[cpu_usage_data['metric'] == 'cpu.ready.summation']
            avg_ready = ready_data['avg_value'].mean()
            st.metric(
                label="Средний CPU Ready (мс)",
                value=f"{avg_ready:.0f}",
                delta="Высокий (>5%)" if avg_ready > 5000 else "Нормальный"
            )
        else:
            st.metric(
                label="Активных ядер",
                value="100%",
                delta="Все серверы"
            )


def create_cpu_usage_trend(cpu_df, selected_servers=None):
    """График тренда использования CPU"""
    usage_data = cpu_df[cpu_df['metric'] == 'cpu.usage.average']

    if selected_servers:
        usage_data = usage_data[usage_data['vm'].isin(selected_servers)]

    # Выбираем топ-10 серверов по максимальной нагрузке
    top_servers = usage_data.groupby('vm')['avg_value'].max().nlargest(10).index
    filtered_data = usage_data[usage_data['vm'].isin(top_servers)]

    fig = px.line(
        filtered_data,
        x='date',
        y='avg_value',
        color='vm',
        title="📈 Динамика CPU нагрузки (топ-10 по пиковой нагрузке)",
        labels={'avg_value': 'CPU нагрузка (%)', 'date': 'Дата', 'vm': 'Сервер'},
        line_shape='spline',
        render_mode='svg',
        hover_data={'avg_value': ':.1f'}
    )

    # Добавляем пороговые линии с анимацией
    fig.add_hline(y=70, line_dash="dash", line_color="red", line_width=2,
                  annotation_text="Критический порог 70%",
                  annotation_position="top left",
                  annotation_font_size=12)

    fig.add_hline(y=20, line_dash="dash", line_color="green", line_width=2,
                  annotation_text="Порог низкой нагрузки 20%",
                  annotation_position="bottom left")

    fig.update_layout(
        height=550,
        hovermode='x unified',
        legend=dict(
            title="Серверы",
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor='rgba(255,255,255,0.8)'
        ),
        xaxis_title="Дата",
        yaxis_title="CPU нагрузка (%)",
        plot_bgcolor='rgba(240, 242, 246, 0.8)',
        title_font_size=16,
        font_size=12
    )

    # Добавляем анимацию для критических значений
    fig.update_traces(
        mode='lines+markers',
        marker=dict(size=6),
        line=dict(width=2)
    )

    return fig


def create_cpu_heatmap(cpu_df):
    """Тепловая карта использования памяти по дням"""
    usage_data = cpu_df[cpu_df['metric'] == 'cpu.usage.average']

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
        labels=dict(x="Дата", y="Сервер", color="Использование cpu (%)"),
        title="Тепловая карта использования cpu",
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


def create_cpu_heatmap_1(cpu_df):
    """Тепловая карта CPU нагрузки по дням"""
    usage_data = cpu_df[cpu_df['metric'] == 'cpu.usage.average']

    pivot_data = usage_data.pivot_table(
        values='avg_value',
        index='vm',
        columns='date',
        aggfunc='mean'
    ).fillna(0)

    # Сортируем по максимальной нагрузке
    pivot_data['max_load'] = pivot_data.max(axis=1)
    pivot_data = pivot_data.sort_values('max_load', ascending=False)
    pivot_data = pivot_data.drop('max_load', axis=1)

    # Кастомная цветовая шкала
    colorscale = [
        [0.0, "#2E8B57"],  # Low - green
        [0.2, "#90EE90"],  # Medium low - light green
        [0.4, "#FFD700"],  # Medium - yellow
        [0.7, "#FF8C00"],  # High - orange
        [1.0, "#FF4500"]  # Critical - red
    ]

    fig = go.Figure(data=go.Heatmap(
        z=pivot_data.values,
        x=pd.to_datetime(pivot_data.columns).strftime('%d.%m'),
        y=[server.split('_')[-1] for server in pivot_data.index],
        colorscale=colorscale,
        colorbar=dict(
            title="CPU %",
            thickness=20,
            len=0.8,
            tickvals=[0, 25, 50, 75, 100],
            ticktext=["0%", "25%", "50%", "75%", "100%"]
        ),
        hoverongaps=False,
        hovertemplate='Сервер: %{y}<br>Дата: %{x}<br>Нагрузка: %{z:.1f}%<extra></extra>'
    ))

    fig.update_layout(
        title="Тепловая карта CPU нагрузки по серверам и дням",
        height=700,
        xaxis_title="Дата",
        yaxis_title="Сервер",
        xaxis=dict(tickangle=45),
        plot_bgcolor='white'
    )

    return fig


def create_cpu_distribution_chart(cpu_df):
    """Гистограмма распределения CPU нагрузки"""
    usage_data = cpu_df[cpu_df['metric'] == 'cpu.usage.average']

    # Берем средние значения за период для каждого сервера
    avg_data = usage_data.groupby('vm')['avg_value'].mean().reset_index()

    # Категоризируем
    bins = [0, 20, 50, 70, 100]
    labels = ['Низкая (<20%)', 'Нормальная (20-50%)', 'Высокая (50-70%)', 'Критическая (>70%)']
    colors = ['#2E8B57', '#FFD700', '#FF8C00', '#FF4500']

    avg_data['category'] = pd.cut(avg_data['avg_value'], bins=bins, labels=labels)

    # Подсчет по категориям
    category_counts = avg_data['category'].value_counts().reindex(labels)

    # Создаем анимированный график
    fig = go.Figure()

    for i, (category, color) in enumerate(zip(labels, colors)):
        count = category_counts[category]
        fig.add_trace(go.Bar(
            x=[category],
            y=[count],
            name=category,
            marker_color=color,
            text=[f"{count}"],
            textposition='auto',
            hovertemplate=f'{category}<br>Количество: {count}<extra></extra>'
        ))

    fig.update_layout(
        title="Распределение серверов по уровню CPU нагрузки",
        height=450,
        xaxis_title="Категория нагрузки",
        yaxis_title="Количество серверов",
        showlegend=False,
        plot_bgcolor='rgba(240, 242, 246, 0.8)',
        bargap=0.2,
        font=dict(size=12)
    )

    # Добавляем аннотации с процентами
    total = category_counts.sum()
    for i, count in enumerate(category_counts):
        percentage = (count / total) * 100
        fig.add_annotation(
            x=i,
            y=count + 0.2,
            text=f"{percentage:.1f}%",
            showarrow=False,
            font=dict(size=11, color='black')
        )

    return fig


def create_cpu_comparison_chart(cpu_df, selected_servers):
    """Сравнение CPU нагрузки нескольких серверов"""
    if not selected_servers:
        selected_servers = cpu_df['vm'].unique()[:4]

    usage_data = cpu_df[
        (cpu_df['metric'] == 'cpu.usage.average') &
        (cpu_df['vm'].isin(selected_servers))
        ]

    # Создаем box plot с violin plot для лучшей визуализации распределения
    fig = go.Figure()

    colors = px.colors.qualitative.Bold

    for i, server in enumerate(selected_servers):
        server_data = usage_data[usage_data['vm'] == server]

        # Box plot
        fig.add_trace(go.Box(
            y=server_data['avg_value'],
            name=server.split('_')[-1],
            boxpoints='all',
            jitter=0.3,
            pointpos=-1.8,
            marker_color=colors[i % len(colors)],
            line_color=colors[i % len(colors)],
            fillcolor='rgba(255,255,255,0.5)',
            hoverinfo='y+name'
        ))

        # Добавляем среднюю линию
        mean_value = server_data['avg_value'].mean()
        fig.add_shape(
            type="line",
            x0=i - 0.4,
            x1=i + 0.4,
            y0=mean_value,
            y1=mean_value,
            line=dict(color="black", width=2, dash="dash"),
            xref="x",
            yref="y"
        )

    fig.update_layout(
        title=f"📊 Сравнение CPU нагрузки ({len(selected_servers)} серверов)",
        yaxis_title="CPU нагрузка (%)",
        xaxis_title="Сервер",
        height=500,
        showlegend=False,
        plot_bgcolor='rgba(240, 242, 246, 0.8)',
        boxmode='group'
    )

    # Пороговые линии
    fig.add_hline(y=70, line_dash="dash", line_color="red", line_width=2,
                  annotation_text="Критический порог 70%",
                  annotation_position="top left")
    fig.add_hline(y=20, line_dash="dot", line_color="green", line_width=1,
                  annotation_text="Порог низкой нагрузки 20%",
                  annotation_position="bottom left")

    return fig


def create_cpu_vs_mhz_chart(cpu_df):
    """График зависимости CPU % от MHz"""
    usage_data = cpu_df[cpu_df['metric'] == 'cpu.usage.average'].copy()
    mhz_data = cpu_df[cpu_df['metric'] == 'cpu.usagemhz.average'].copy()

    # Объединяем данные
    combined = pd.merge(
        usage_data[['vm', 'date', 'avg_value']],
        mhz_data[['vm', 'date', 'avg_value']],
        on=['vm', 'date'],
        suffixes=('_cpu', '_mhz')
    )

    fig = px.scatter(
        combined,
        x='avg_value_mhz',
        y='avg_value_cpu',
        color='vm',
        title="⚡ Зависимость CPU % от MHz использования",
        labels={'avg_value_mhz': 'MHz использования', 'avg_value_cpu': 'CPU нагрузка (%)'},
        hover_name='vm',
        size_max=15
    )

    # Добавляем линию регрессии
    fig.update_traces(
        marker=dict(size=8, opacity=0.7),
        selector=dict(mode='markers')
    )

    fig.update_layout(
        height=500,
        xaxis_title="Использование MHz",
        yaxis_title="CPU нагрузка (%)",
        legend=dict(
            title="Серверы",
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.02
        ),
        plot_bgcolor='rgba(240, 242, 246, 0.8)'
    )

    return fig


def create_detailed_cpu_analysis(cpu_df, selected_server):
    """Детальный анализ CPU для выбранного сервера"""
    server_data = cpu_df[cpu_df['vm'] == selected_server]

    # Разные метрики CPU
    metrics_data = {}
    for metric in ['cpu.usage.average', 'cpu.usagemhz.average', 'cpu.ready.summation']:
        metric_data = server_data[server_data['metric'] == metric]
        if not metric_data.empty:
            metrics_data[metric] = metric_data

    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=[
            'CPU нагрузка (%)',
            'Использование MHz',
            'CPU Ready время (мс)'
        ],
        vertical_spacing=0.12,
        shared_xaxes=True
    )

    # CPU Usage
    if 'cpu.usage.average' in metrics_data:
        data = metrics_data['cpu.usage.average']
        fig.add_trace(
            go.Scatter(
                x=data['date'],
                y=data['avg_value'],
                mode='lines+markers',
                name='CPU %',
                line=dict(color='blue', width=3),
                fill='tozeroy',
                fillcolor='rgba(0, 100, 255, 0.1)'
            ),
            row=1, col=1
        )
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=1, col=1)

    # MHz Usage
    if 'cpu.usagemhz.average' in metrics_data:
        data = metrics_data['cpu.usagemhz.average']
        fig.add_trace(
            go.Scatter(
                x=data['date'],
                y=data['avg_value'],
                mode='lines+markers',
                name='MHz',
                line=dict(color='green', width=2)
            ),
            row=2, col=1
        )

    # CPU Ready
    if 'cpu.ready.summation' in metrics_data:
        data = metrics_data['cpu.ready.summation']
        fig.add_trace(
            go.Scatter(
                x=data['date'],
                y=data['avg_value'],
                mode='lines+markers',
                name='CPU Ready',
                line=dict(color='orange', width=2)
            ),
            row=3, col=1
        )
        fig.add_hline(y=5000, line_dash="dash", line_color="red", row=3, col=1,
                      annotation_text="Высокий CPU Ready (>5%)")

    fig.update_layout(
        height=800,
        title_text=f"🔍 Детальный анализ CPU: {selected_server}",
        showlegend=True,
        hovermode='x unified'
    )

    fig.update_xaxes(title_text="Дата", row=3, col=1)

    return fig


def create_peak_cpu_usage_table(cpu_df):
    """Таблица пикового использования CPU"""
    usage_data = cpu_df[cpu_df['metric'] == 'cpu.usage.average']

    peak_usage = usage_data.groupby('vm').agg({
        'avg_value': ['max', 'mean', 'min', 'std'],
        'date': lambda x: x.iloc[usage_data.loc[x.index, 'avg_value'].idxmax()].strftime('%d.%m')
    }).round(2)

    peak_usage.columns = ['Пик (%)', 'Среднее (%)', 'Минимум (%)', 'Станд. отклонение', 'Дата пика']
    peak_usage = peak_usage.sort_values('Пик (%)', ascending=False)

    # Добавляем цветовую маркировку
    def color_cells(val):
        if isinstance(val, (int, float)):
            if val > 70:
                return 'background-color: #ff6b6b; color: white; font-weight: bold;'
            elif val > 50:
                return 'background-color: #ffd166;'
            elif val < 20:
                return 'background-color: #06d6a0; color: white;'
        return ''

    styled_table = peak_usage.style.applymap(color_cells,
                                             subset=['Пик (%)', 'Среднее (%)', 'Минимум (%)'])

    # Форматирование
    styled_table = styled_table.format({
        'Пик (%)': '{:.1f}%',
        'Среднее (%)': '{:.1f}%',
        'Минимум (%)': '{:.1f}%',
        'Станд. отклонение': '{:.2f}'
    })

    return styled_table


def create_performance_issues_table(cpu_df):
    """Тацаблица производительности с CPU Ready"""
    usage_data = cpu_df[cpu_df['metric'] == 'cpu.usage.average']
    ready_data = cpu_df[cpu_df['metric'] == 'cpu.ready.summation']

    issues = []

    for server in cpu_df['vm'].unique():
        server_usage = usage_data[usage_data['vm'] == server]
        server_ready = ready_data[ready_data['vm'] == server]

        if not server_usage.empty:
            max_cpu = server_usage['avg_value'].max()
            avg_cpu = server_usage['avg_value'].mean()

            if not server_ready.empty:
                max_ready = server_ready['avg_value'].max()
                issue_level = []

                if max_cpu > 70:
                    issue_level.append("🔴 Высокая CPU")
                elif max_cpu < 20:
                    issue_level.append("🟢 Низкая CPU")

                if max_ready > 5000:  # 5% CPU Ready
                    issue_level.append("⚠️ Высокий CPU Ready")

                if issue_level:
                    issues.append({
                        'Сервер': server.split('_')[-1],
                        'Макс. CPU': f"{max_cpu:.1f}%",
                        'Ср. CPU': f"{avg_cpu:.1f}%",
                        'Макс. CPU Ready': f"{max_ready:.0f} мс",
                        'Проблемы': " | ".join(issue_level)
                    })

    return pd.DataFrame(issues)


def main():
    # Заголовок
    st.markdown("""
    <div class="cpu-header">
        <h1>⚡ Анализ CPU нагрузки серверов</h1>
        <p>Период: 2025-11-25 — 2025-12-01 | Мониторинг производительности и проблем</p>
    </div>
    """, unsafe_allow_html=True)

    # Загрузка данных
    with st.spinner('Загрузка данных CPU...'):
        cpu_df, cpu_usage_data = load_cpu_data()

    # Боковая панель
    with st.sidebar:
        st.header("⚙️ Настройки анализа")

        # Выбор серверов
        all_servers = sorted(cpu_df['vm'].unique())
        selected_servers = st.multiselect(
            "Выберите серверы для анализа:",
            all_servers,
            default=all_servers[:3]
        )

        # Выбор сервера для детального анализа
        selected_detailed_server = st.selectbox(
            "Сервер для детального анализа:",
            all_servers,
            index=0
        )

        # Фильтр по датам
        min_date = cpu_df['date'].min()
        max_date = cpu_df['date'].max()

        date_range = st.date_input(
            "Диапазон дат:",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )

        if len(date_range) == 2:
            start_date, end_date = date_range
            cpu_df = cpu_df[
                (cpu_df['date'] >= pd.Timestamp(start_date)) &
                (cpu_df['date'] <= pd.Timestamp(end_date))
                ]

        # Настройки порогов
        st.subheader("📊 Настройка порогов")
        critical_threshold = st.slider("Критический порог CPU (%)", 50, 95, 70)
        warning_threshold = st.slider("Предупреждение CPU (%)", 30, 80, 50)

        st.subheader("📈 Отображение графиков")
        show_heatmap = st.checkbox("Тепловая карта", value=True)
        show_distribution = st.checkbox("Распределение", value=True)
        show_comparison = st.checkbox("Сравнение серверов", value=True)
        show_correlation = st.checkbox("CPU vs MHz", value=False)

    # Основные метрики
    create_cpu_summary_cards(cpu_usage_data)

    # Первый ряд графиков
    if show_distribution or show_comparison:
        col1, col2 = st.columns(2)

        with col1:
            if show_distribution:
                st.plotly_chart(
                    create_cpu_distribution_chart(cpu_df),
                    use_container_width=True
                )

        with col2:
            if show_comparison and selected_servers:
                st.plotly_chart(
                    create_cpu_comparison_chart(cpu_df, selected_servers),
                    use_container_width=True
                )

    # Тепловая карта
    if show_heatmap:
        st.plotly_chart(
            create_cpu_heatmap(cpu_df),
            use_container_width=True
        )

    # График тренда
    st.plotly_chart(
        create_cpu_usage_trend(cpu_df, selected_servers),
        use_container_width=True
    )

    # График корреляции
    if show_correlation:
        st.plotly_chart(
            create_cpu_vs_mhz_chart(cpu_df),
            use_container_width=True
        )

    # Таблицы
    col3, col4 = st.columns(2)

    with col3:
        st.header("📋 Таблица пикового использования CPU")
        peak_table = create_peak_cpu_usage_table(cpu_df)
        st.dataframe(
            peak_table,
            use_container_width=True,
            height=400
        )

    with col4:
        st.header("⚠️ Проблемы производительности")
        issues_table = create_performance_issues_table(cpu_df)
        if not issues_table.empty:
            st.dataframe(
                issues_table,
                use_container_width=True,
                height=400
            )
        else:
            st.success("✅ Проблем с производительностью не обнаружено")

    # Детальный анализ
    st.header(f"🔍 Детальный анализ: {selected_detailed_server}")
    detailed_fig = create_detailed_cpu_analysis(cpu_df, selected_detailed_server)
    st.plotly_chart(detailed_fig, use_container_width=True)

    # Предупреждения и рекомендации
    st.header("🚨 Критические ситуации")

    # Серверы с высокой нагрузкой
    usage_data = cpu_df[cpu_df['metric'] == 'cpu.usage.average']
    critical_servers = usage_data.groupby('vm')['avg_value'].max()
    critical_servers = critical_servers[critical_servers > critical_threshold]

    if not critical_servers.empty:
        st.markdown("""
        <div class="critical-card">
            <h4>🔴 Серверы с критической CPU нагрузкой (>70%):</h4>
        </div>
        """, unsafe_allow_html=True)

        for server, usage in critical_servers.items():
            server_name = server.split('_')[-1]
            st.markdown(f"""
            <div class="threshold-line">
                <strong>{server_name}</strong>: {usage:.1f}% CPU
                <span style="color: #ff6b6b; font-weight: bold;">→ Требуется масштабирование</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="success-card">
            <h4>✅ Нет серверов с критической CPU нагрузкой</h4>
        </div>
        """, unsafe_allow_html=True)

    # Недогруженные серверы
    underutilized_servers = usage_data.groupby('vm')['avg_value'].mean()
    underutilized_servers = underutilized_servers[underutilized_servers < 20]

    if not underutilized_servers.empty:
        st.markdown("""
        <div class="warning-card">
            <h4>🟢 Недогруженные серверы (<20% CPU):</h4>
        </div>
        """, unsafe_allow_html=True)

        servers_html = "".join([f'<span class="server-tag">{s.split("_")[-1]}</span>'
                                for s in underutilized_servers.index])
        st.markdown(servers_html, unsafe_allow_html=True)
        st.caption("⚡ Эти серверы могут быть кандидатами для консолидации виртуальных машин.")

    # Экспорт данных
    st.markdown("---")
    st.header("📥 Экспорт данных")

    col5, col6 = st.columns(2)

    with col5:
        # Экспорт всех данных CPU
        cpu_csv = cpu_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Все данные CPU (CSV)",
            data=cpu_csv,
            file_name="cpu_usage_data.csv",
            mime="text/csv",
            help="Скачать полные данные мониторинга CPU"
        )

    with col6:
        # Экспорт отчета о проблемах
        if not issues_table.empty:
            issues_csv = issues_table.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Отчет о проблемах (CSV)",
                data=issues_csv,
                file_name="cpu_issues_report.csv",
                mime="text/csv",
                help="Скачать отчет о проблемах производительности"
            )

        # Кнопка для генерации PDF отчета
        if st.button("📄 Сгенерировать PDF отчет"):
            st.info("Функция генерации PDF будет реализована в следующей версии")

    # Информация о данных
    with st.expander("📊 Информация о метриках CPU"):
        st.markdown("""
        ### Метрики CPU:

        **cpu.usage.average** - Средняя загрузка CPU в процентах
        - <20%: Низкая нагрузка
        - 20-70%: Нормальная нагрузка
        - >70%: Высокая нагрузка

        **cpu.usagemhz.average** - Использование CPU в MHz
        - Показывает абсолютное использование вычислительной мощности

        **cpu.ready.summation** - Время ожидания CPU (CPU Ready)
        - <1000 мс: Нормально
        - 1000-5000 мс: Предупреждение
        - >5000 мс: Проблема (высокий CPU Ready)

        ### Рекомендации:
        1. Серверы с CPU >70% требуют мониторинга и возможного масштабирования
        2. Серверы с CPU <20% могут быть объединены для экономии ресурсов
        3. Высокий CPU Ready указывает на нехватку физических CPU ресурсов
        """)


if __name__ == "__main__":
    main()