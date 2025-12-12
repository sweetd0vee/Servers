import pandas as pd
import streamlit as st
from database import get_db_connection, close_db_connection
import io


def import_from_excel_to_db(file_path, source_type="excel"):
    """Импорт данных из Excel файла в базу данных"""
    try:
        # Читаем Excel файл
        df = pd.read_excel(file_path)

        # Проверяем необходимые колонки
        required_columns = ['vm', 'date', 'metric', 'max_value', 'min_value', 'avg_value']
        missing_cols = [col for col in required_columns if col not in df.columns]

        if missing_cols:
            st.error(f"Отсутствуют обязательные колонки: {missing_cols}")
            return 0, False

        # Подключаемся к базе
        conn = get_db_connection()
        if not conn:
            st.error("Не удалось подключиться к базе данных")
            return 0, False

        cursor = conn.cursor()

        # SQL для вставки или обновления данных
        insert_sql = """
        INSERT INTO server_metrics (vm, date, metric, max_value, min_value, avg_value)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (vm, date, metric) 
        DO UPDATE SET 
            max_value = EXCLUDED.max_value,
            min_value = EXCLUDED.min_value,
            avg_value = EXCLUDED.avg_value,
            updated_at = CURRENT_TIMESTAMP
        """

        # SQL для логирования импорта
        log_sql = """
        INSERT INTO data_import_log (source_type, records_count, status)
        VALUES (%s, %s, %s)
        """

        success_count = 0
        error_count = 0

        # Вставляем данные построчно
        for _, row in df.iterrows():
            try:
                # Преобразуем дату
                date_val = pd.to_datetime(row['date']).date()

                # Вставляем данные
                cursor.execute(insert_sql, (
                    str(row['vm']),
                    date_val,
                    str(row['metric']),
                    float(row['max_value']) if pd.notna(row['max_value']) else None,
                    float(row['min_value']) if pd.notna(row['min_value']) else None,
                    float(row['avg_value']) if pd.notna(row['avg_value']) else None
                ))
                success_count += 1

            except Exception as row_error:
                error_count += 1
                st.warning(f"Ошибка в строке {_}: {row_error}")
                continue

        # Логируем импорт
        status = "success" if error_count == 0 else "partial"
        cursor.execute(log_sql, (source_type, success_count, status))

        conn.commit()

        # Закрываем подключение
        cursor.close()
        conn.close()

        return success_count, error_count

    except Exception as e:
        st.error(f"Ошибка при импорте данных: {e}")
        return 0, 0


def import_from_dataframe(df, source_type="manual"):
    """Импорт данных из DataFrame в базу"""
    try:
        conn = get_db_connection()
        if not conn:
            return 0, 0

        cursor = conn.cursor()

        insert_sql = """
        INSERT INTO server_metrics (vm, date, metric, max_value, min_value, avg_value)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (vm, date, metric) 
        DO UPDATE SET 
            max_value = EXCLUDED.max_value,
            min_value = EXCLUDED.min_value,
            avg_value = EXCLUDED.avg_value,
            updated_at = CURRENT_TIMESTAMP
        """

        success_count = 0

        for _, row in df.iterrows():
            try:
                cursor.execute(insert_sql, (
                    str(row['vm']),
                    row['date'].date() if hasattr(row['date'], 'date') else row['date'],
                    str(row['metric']),
                    float(row['max_value']) if pd.notna(row['max_value']) else None,
                    float(row['min_value']) if pd.notna(row['min_value']) else None,
                    float(row['avg_value']) if pd.notna(row['avg_value']) else None
                ))
                success_count += 1
            except:
                continue

        conn.commit()
        cursor.close()
        conn.close()

        return success_count, 0

    except Exception as e:
        st.error(f"Ошибка импорта: {e}")
        return 0, 0


def create_import_section():
    """Создание секции импорта данных в интерфейсе"""
    st.markdown("---")
    st.header("Импорт данных в базу")

    col1, col2 = st.columns([2, 1])

    with col1:
        uploaded_file = st.file_uploader(
            "Загрузите Excel файл с метриками",
            type=['xlsx', 'xls'],
            help="Файл должен содержать колонки: vm, date, metric, max_value, min_value, avg_value"
        )

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📤 Импортировать в БД", use_container_width=True):
            if uploaded_file is not None:
                with st.spinner("Импорт данных..."):
                    # Сохраняем файл временно
                    with open("temp_upload.xlsx", "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    # Импортируем в базу
                    success_count, error_count = import_from_excel_to_db("temp_upload.xlsx")

                    if success_count > 0:
                        st.success(f"✅ Успешно импортировано: {success_count} записей")
                        if error_count > 0:
                            st.warning(f"⚠️ С ошибками: {error_count} записей")
                    else:
                        st.error("❌ Не удалось импортировать данные")
            else:
                st.warning("Пожалуйста, загрузите файл")

    # Отображение истории импорта
    with st.expander("📋 История импорта"):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT import_date, source_type, records_count, status 
                FROM data_import_log 
                ORDER BY import_date DESC 
                LIMIT 10
            """)

            logs = cursor.fetchall()

            if logs:
                log_df = pd.DataFrame(logs, columns=['Дата импорта', 'Источник', 'Кол-во записей', 'Статус'])
                st.dataframe(log_df, use_container_width=True)
            else:
                st.info("Нет записей об импорте")

            cursor.close()
            conn.close()

        except Exception as e:
            st.warning(f"Не удалось загрузить историю: {e}")