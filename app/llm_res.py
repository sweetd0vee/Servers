# app.py
import streamlit as st
import pandas as pd
#from openai import OpenAI
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Анализатор нагрузки серверов", layout="wide")

st.title("📊 Анализатор нагрузки серверов с LLM")
st.markdown("---")

# Загрузка файла
uploaded_file = st.file_uploader("Загрузите CSV файл", type=['csv'])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Показ данных
    st.subheader("Исходные данные")
    st.dataframe(df, use_container_width=True)

    # Визуализация
    col1, col2 = st.columns(2)

    with col1:
        fig = px.scatter(df, x='Средний CPU %', y='Средняя Memory %',
                         hover_data=['Сервер'],
                         title='Распределение нагрузки')
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Категории нагрузки
        fig = go.Figure()

        for category in df['CPU Категория'].unique():
            subset = df[df['CPU Категория'] == category]
            fig.add_trace(go.Box(
                y=subset['Средний CPU %'],
                name=category,
                boxpoints='all'
            ))

        fig.update_layout(title='Распределение CPU по категориям')
        st.plotly_chart(fig, use_container_width=True)

    # Анализ через LLM
    st.subheader("🔍 Глубокий анализ через LLM")

    api_key = st.text_input("Введите OpenAI API ключ", type="password")
    selected_server = st.selectbox("Выберите сервер для детального анализа", df['Сервер'].tolist())

    if api_key and selected_server:
        if st.button("Проанализировать выбранный сервер"):
            with st.spinner("Анализ через GPT..."):
                client = OpenAI(api_key=api_key)

                server_data = df[df['Сервер'] == selected_server].iloc[0]

                prompt = f"""
                Дай детальный анализ сервера:

                Имя: {server_data['Сервер']}
                CPU: {server_data['Средний CPU %']}%
                Память: {server_data['Средняя Memory %']}%
                Рекомендация в данных: {server_data.get('Рекомендация', 'Нет')}

                Ответь на вопросы:
                1. Какая возможная причина такой нагрузки?
                2. Какие риски?
                3. Какие конкретные действия рекомендованы?
                4. Можно ли консолидировать с другими серверами?
                """

                response = client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[
                        {"role": "system", "content": "Ты DevOps эксперт."},
                        {"role": "user", "content": prompt}
                    ]
                )

                analysis = response.choices[0].message.content

                st.markdown("### 📋 Результат анализа")
                st.write(analysis)

                # Сохранение в сессии
                if 'analyses' not in st.session_state:
                    st.session_state.analyses = {}
                st.session_state.analyses[selected_server] = analysis

    # Экспорт результатов
    if st.button("📥 Сгенерировать полный отчет"):
        st.download_button(
            label="Скачать отчет Excel",
            data=df.to_csv(index=False).encode('utf-8-sig'),
            file_name="server_analysis_report.csv",
            mime="text/csv"
        )

# Запуск: streamlit run app.py