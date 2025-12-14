"""
Скрипт для инициализации базы данных и загрузки данных из Excel
"""
import pandas as pd
from sqlalchemy import create_engine
from database.connection import Base, engine, DATABASE_URL
from database.models import ServerMetrics
import uuid
from datetime import datetime
import os
import sys

# Добавляем путь для импорта логгера
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
        logger.error(f"Ошибка при создании таблиц: {e}")
        return False


def validate_and_transform_data(df):
    """Проверка и преобразование данных из Excel"""
    # Требуемые колонки в модели
    required_columns = ['vm', 'date', 'metric', 'max_value', 'min_value', 'avg_value']

    # Проверяем наличие необходимых колонок
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Отсутствуют необходимые колонки: {missing_columns}")

    # Преобразуем типы данных
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])

    # Преобразуем числовые колонки
    numeric_columns = ['max_value', 'min_value', 'avg_value']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df


def load_excel_to_db(excel_path="../data/metrics.xlsx"):
    """Загрузка данных из Excel в базу данных"""
    logger.info(f"Загрузка данных из {excel_path}...")

    try:
        # Чтение Excel файла
        df = pd.read_excel(excel_path)
        logger.info(f"Прочитано {len(df)} записей из Excel")

        # Проверяем и преобразуем данные
        df = validate_and_transform_data(df)

        # Добавляем необходимые поля для модели
        df['id'] = [uuid.uuid4() for _ in range(len(df))]

        # Создаем подключение к базе данных
        engine_db = create_engine(DATABASE_URL)

        # Загружаем данные в таблицу server_metrics
        with engine_db.begin() as connection:
            # Очищаем таблицу перед загрузкой
            connection.execute("TRUNCATE TABLE server_metrics RESTART IDENTITY CASCADE;")

            # Загружаем данные
            df.to_sql(
                'server_metrics',
                connection,
                if_exists='append',
                index=False,
                method='multi'  # Для более быстрой загрузки
            )

        logger.info(f"Данные успешно загружены ({len(df)} записей)")
        return True

    except FileNotFoundError:
        logger.error(f"Файл {excel_path} не найден")
        return False
    except ValueError as e:
        logger.error(f"Ошибка валидации данных: {e}")
        return False
    except Exception as e:
        logger.error(f"Ошибка при загрузке данных: {e}")
        return False


def check_excel_structure(excel_path):
    """Проверка структуры Excel файла"""
    try:
        df = pd.read_excel(excel_path)
        print("\n" + "="*50)
        print("СТРУКТУРА EXCEL ФАЙЛА:")
        print("="*50)
        print(f"Колонки: {list(df.columns)}")
        print(f"Всего записей: {len(df)}")
        print("\nПервые 5 строк:")
        print(df.head())
        print("\nТипы данных:")
        print(df.dtypes)
        print("="*50)

        return True
    except Exception as e:
        print(f"Ошибка при чтении файла: {e}")
        return False


def main():
    """Основная функция"""
    print("=" * 50)
    print("ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ СЕРВЕРНОГО МОНИТОРИНГА")
    print("=" * 50)

    # Создаем таблицы
    if not init_database():
        return

    # Запрашиваем путь к Excel файлу
    excel_path = input("Введите путь к Excel файлу (по умолчанию ../data/metrics.xlsx): ").strip()
    if not excel_path:
        excel_path = "../data/metrics.xlsx"

    # Проверяем существование файла
    if not os.path.exists(excel_path):
        logger.error(f"Файл {excel_path} не найден")
        print(f"\nПожалуйста, создайте файл {excel_path} со следующей структурой:")
        print("Обязательные колонки: vm, date, metric, max_value, min_value, avg_value")
        print("Пример данных:")
        print("vm,date,metric,max_value,min_value,avg_value")
        print("server1,2024-01-01,cpu_usage,95.5,10.2,45.3")
        print("server1,2024-01-01,memory_usage,85.0,20.1,50.5")
        return

    # Показываем структуру Excel файла
    if not check_excel_structure(excel_path):
        return

    # Подтверждение загрузки
    confirm = input("\nЗагрузить данные в базу? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Загрузка отменена")
        return

    # Загружаем данные из Excel
    if not load_excel_to_db(excel_path):
        return

    print("\n" + "=" * 50)
    print("Инициализация завершена успешно!")
    print(f"База данных: {DATABASE_URL}")
    print("=" * 50)


if __name__ == "__main__":
    main()