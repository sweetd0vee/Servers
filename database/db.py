import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Конфигурация базы данных PostgreSQL
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'server_metrics'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres')
}

# SQL для создания таблицы
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS server_metrics (
    id SERIAL PRIMARY KEY,
    vm VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    metric VARCHAR(100) NOT NULL,
    max_value NUMERIC,
    min_value NUMERIC,
    avg_value NUMERIC,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vm, date, metric)
);
"""

CREATE_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_metrics_vm_date 
ON server_metrics(vm, date, metric);
"""


def get_db_connection():
    """Создание подключения к базе данных"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return None


def close_db_connection(conn, cursor=None):
    """Закрытие подключения к базе данных"""
    try:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    except Exception as e:
        print(f"Ошибка при закрытии подключения: {e}")
