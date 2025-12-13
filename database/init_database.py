"""
Скрипт для инициализации базы данных и загрузки данных из Excel
"""
import pandas as pd
from sqlalchemy import create_engine
from database.connection import Base, engine, DATABASE_URL
from database.models import Servers
import uuid
from datetime import datetime
import os

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_logger import logger


def init_database():
    """Инициализация базы данных"""
    logger.info("Создание таблиц в базе данных...")

    try:
        # Создаем все таблицы
        Base.metadata.create_all(bind=engine)
        logger.info("Таблицы созданы успешно!")
        return True
    except Exception as e:
        logger.info(f"Ошибка при создании таблиц: {e}")
        return False


def load_excel_to_db(excel_path="../data/metrics.xlsx"):
    """Загрузка данных из Excel в базу данных"""
    print(f"Загрузка данных из {excel_path}...")

    try:
        # Чтение Excel файла
        df = pd.read_excel(excel_path)

        # Создаем соединение
        engine = create_engine(DATABASE_URL)

        # Загружаем данные в базу
        df.to_sql('servers', engine, if_exists='replace', index=False)

        print(f"Данные успешно загружены ({len(df)} записей)")
        return True
    except FileNotFoundError:
        print(f"Файл {excel_path} не найден")
        return False
    except Exception as e:
        print(f"Ошибка при загрузке данных: {e}")
        return False


def main():
    """Основная функция"""
    print("=" * 50)
    print("ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ СЕРВЕРНОГО МОНИТОРИНГА")
    print("=" * 50)

    # Создаем таблицы
    if not init_database():
        return

    # Загружаем данные из Excel
    excel_path = input("Введите путь к Excel файлу (по умолчанию data/metrics.xlsx): ").strip()
    if not excel_path:
        excel_path = "../data/metrics.xlsx"

    if not load_excel_to_db(excel_path):
        return

    print("\n" + "=" * 50)
    print("Инициализация завершена успешно!")
    print(f"База данных: {DATABASE_URL}")
    print("=" * 50)


if __name__ == "__main__":
    main()