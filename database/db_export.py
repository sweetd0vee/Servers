import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from db import get_db_connection, close_db_connection
import io


def export_data_from_db(filters=None):
    """Экспорт данных из базы с возможными фильтрами"""
    try:
        conn = get_db_connection()
        if not conn:
            return pd.DataFrame()

        cursor = conn.cursor()

        # Базовый SQL запрос
        base_sql = """
        SELECT 
            vm,
            date,
            metric,
            max_value,
            min_value,
            avg_value,
            updated_at
        FROM server_metrics
        WHERE 1=1
        """

        params = []

        # Добавляем фильтры
        if filters:
            if 'vm' in filters and filters['vm']:
                base_sql += " AND vm = %s"
                params.append(filters['vm'])

            if 'start_date' in filters and filters['start_date']:
                base_sql += " AND date >= %s"
                params.append(filters['start_date'])

            if 'end_date' in filters and filters['end_date']:
                base_sql += " AND date <= %s"
                params.append(filters['end_date'])

            if 'metric' in filters and filters['metric']:
                base_sql += " AND metric LIKE %s"
                params.append(f'%{filters["metric"]}%')

        # Сортировка
        base_sql += " ORDER BY vm, date, metric"

        # Выполняем запрос
        cursor.execute(base_sql, params)

        # Получаем данные
        columns = ['vm', 'date', 'metric', 'max_value', 'min_value', 'avg_value', 'updated_at']
        data = cursor.fetchall()

        # Создаем DataFrame
        df = pd.DataFrame(data, columns=columns)

        cursor.close()
        conn.close()

        return df

    except Exception as e:
        st.error(f"Ошибка при экспорте данных: {e}")
        return pd.DataFrame()


def export_to_excel(df, filename="server_metrics_export.xlsx"):
    """Экспорт DataFrame в Excel файл"""
    try:
        # Создаем байтовый поток
        output = io.BytesIO()

        # Используем ExcelWriter с движком openpyxl
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Metrics')

            # Добавляем сводный лист
            if not df.empty:
                summary_df = create_summary_dataframe(df)
                summary_df.to_excel(writer, index=False, sheet_name='Summary')

        output.seek(0)

        return output

    except Exception as e:
        st.error(f"Ошибка при создании Excel файла: {e}")
        return None


def create_summary_dataframe(df):
    """Создание сводной таблицы"""
    if df.empty:
        return pd.DataFrame()

    try:
        # Анализ CPU
        cpu_data = df[df['metric'].str.contains('cpu.usage', case=False, na=False)]
        cpu_summary = cpu_data.groupby('vm').agg({
            'avg_value': ['mean', 'max', 'min'],
            'date': 'nunique'
        }).round(2)

        # Анализ памяти
        mem_data = df[df['metric'].str.contains('mem.usage', case=False, na=False)]
        mem_summary = mem_data.groupby('vm').agg({
            'avg_value': ['mean', 'max', 'min'],
            'date': 'nunique'
        }).round(2)

        # Объединяем результаты
        summary = pd.concat([
            cpu_summary.rename(columns={'avg_value': 'CPU_avg', 'date': 'CPU_days'}),
            mem_summary.rename(columns={'avg_value': 'Memory_avg', 'date': 'Memory_days'})
        ], axis=1)

        # Добавляем классификацию
        summary['CPU_status'] = summary[('CPU_avg', 'mean')].apply(
            lambda x: 'Высокая' if x > 70 else ('Низкая' if x < 20 else 'Нормальная')
        )

        summary['Memory_status'] = summary[('Memory_avg', 'mean')].apply(
            lambda x: 'Высокая' if x > 80 else ('Низкая' if x < 30 else 'Нормальная')
        )

        # Переименовываем колонки
        summary.columns = ['_'.join(col).strip() for col in summary.columns.values]

        return summary.reset_index()

    except Exception as e:
        st.warning(f"Не удалось создать сводную таблицу: {e}")
        return pd.DataFrame()


def create_export_section():
    """Создание секции экспорта данных в интерфейсе"""
    st.markdown("---")
    st.header("Экспорт данных из базы")

    # Фильтры для экспорта
    col1, col2, col3 = st.columns(3)

    filters = {}

    with col1:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT DISTINCT vm FROM server_metrics ORDER BY vm")
            vms = [row[0] for row in cursor.fetchall()]

            cursor.execute("SELECT DISTINCT metric FROM server_metrics WHERE metric LIKE '%.usage.%' ORDER BY metric")
            metrics = [row[0] for row in cursor.fetchall()]

            cursor.close()
            conn.close()

            filters['vm'] = st.selectbox(
                "Сервер (опционально)",
                [""] + vms,
                help="Оставьте пустым для всех серверов"
            )

            filters['metric'] = st.selectbox(
                "Метрика (опционально)",
                [""] + metrics,
                help="Оставьте пустым для всех метрик"
            )

        except Exception as e:
            st.warning(f"Не удалось загрузить список серверов: {e}")

    with col2:
        # Дата начала
        start_date = st.date_input(
            "Дата начала",
            value=datetime.now().date() - timedelta(days=30),
            help="Выберите начальную дату"
        )
        filters['start_date'] = start_date

    with col3:
        # Дата окончания
        end_date = st.date_input(
            "Дата окончания",
            value=datetime.now().date(),
            help="Выберите конечную дату"
        )
        filters['end_date'] = end_date

    # Кнопки экспорта
    col_export1, col_export2, col_export3 = st.columns(3)

    with col_export1:
        if st.button("📋 Предварительный просмотр", use_container_width=True):
            with st.spinner("Загрузка данных..."):
                df = export_data_from_db(filters)
                if not df.empty:
                    st.dataframe(df.head(100), use_container_width=True)
                    st.info(f"Всего записей: {len(df):,}")
                else:
                    st.warning("Нет данных для отображения")

    with col_export2:
        if st.button("📊 Экспорт в CSV", use_container_width=True):
            with st.spinner("Подготовка данных..."):
                df = export_data_from_db(filters)
                if not df.empty:
                    csv = df.to_csv(index=False).encode('utf-8')

                    st.download_button(
                        label="💾 Скачать CSV",
                        data=csv,
                        file_name=f"server_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                else:
                    st.warning("Нет данных для экспорта")

    with col_export3:
        if st.button("📗 Экспорт в Excel", use_container_width=True):
            with st.spinner("Создание Excel файла..."):
                df = export_data_from_db(filters)
                if not df.empty:
                    excel_data = export_to_excel(df)

                    if excel_data:
                        st.download_button(
                            label="💾 Скачать Excel",
                            data=excel_data,
                            file_name=f"server_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                else:
                    st.warning("Нет данных для экспорта")