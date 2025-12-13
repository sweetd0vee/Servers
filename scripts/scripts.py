# SQL для вставки или обновления данных
INSERT_SQL = """
    INSERT INTO servers (vm, date, metric, max_value, min_value, avg_value)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (vm, date, metric) 
    DO UPDATE SET 
        max_value = EXCLUDED.max_value,
        min_value = EXCLUDED.min_value,
        avg_value = EXCLUDED.avg_value,
        updated_at = CURRENT_TIMESTAMP
    """

# SQL для логирования импорта
LOG_SQL = """
    INSERT INTO data_import_log (source_type, records_count, status)
    VALUES (%s, %s, %s)
"""

# Базовый SQL запрос
BASE_SQL = """
SELECT 
    vm,
    date,
    metric,
    max_value,
    min_value,
    avg_value,
    updated_at
FROM servers
WHERE 1=1
"""