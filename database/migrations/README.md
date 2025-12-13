# Database Migrations

Этот каталог содержит миграции базы данных, управляемые через Alembic.

## Структура

```
migrations/
├── env.py              # Конфигурация Alembic
├── script.py.mako      # Шаблон для миграций
├── versions/           # Файлы миграций
│   ├── 001_initial_create_server_metrics.py
│   └── ...
└── README.md           # Эта документация
```

## Быстрый старт

### 1. Инициализация (если еще не сделано)

```bash
# Установите зависимости
pip install alembic

# Инициализация уже выполнена, но если нужно переинициализировать:
alembic -c database/alembic.ini init database/migrations
```

### 2. Создание новой миграции

```bash
# Автоматическое создание миграции на основе изменений моделей
alembic -c database/alembic.ini revision --autogenerate -m "Описание изменений"

# Ручное создание пустой миграции
alembic -c database/alembic.ini revision -m "Описание изменений"
```

### 3. Применение миграций

```bash
# Применить все миграции до последней версии
alembic -c database/alembic.ini upgrade head

# Применить конкретную миграцию
alembic -c database/alembic.ini upgrade <revision_id>

# Откатить одну миграцию
alembic -c database/alembic.ini downgrade -1

# Откатить все миграции
alembic -c database/alembic.ini downgrade base
```

### 4. Просмотр статуса

```bash
# Текущая версия БД
alembic -c database/alembic.ini current

# История миграций
alembic -c database/alembic.ini history

# Показать SQL для миграции (без применения)
alembic -c database/alembic.ini upgrade head --sql
```

## Примеры использования

### Создание миграции для добавления новой колонки

1. Измените модель в `database/table.py`:

```python
class ServerMetrics(Base):
    # ... существующие поля ...
    new_field = Column(String(100), nullable=True)  # Новое поле
```

2. Создайте миграцию:

```bash
alembic -c database/alembic.ini revision --autogenerate -m "Add new_field to server_metrics"
```

3. Проверьте созданную миграцию в `versions/`

4. Примените миграцию:

```bash
alembic -c database/alembic.ini upgrade head
```

### Создание миграции для изменения типа данных

1. Создайте миграцию вручную:

```bash
alembic -c database/alembic.ini revision -m "Change metric column type"
```

2. Отредактируйте файл миграции:

```python
def upgrade() -> None:
    op.alter_column('server_metrics', 'metric',
                    existing_type=sa.String(length=100),
                    type_=sa.String(length=200),
                    nullable=False)

def downgrade() -> None:
    op.alter_column('server_metrics', 'metric',
                    existing_type=sa.String(length=200),
                    type_=sa.String(length=100),
                    nullable=False)
```

3. Примените миграцию:

```bash
alembic -c database/alembic.ini upgrade head
```

## Важные замечания

### ⚠️ Автогенерация миграций

Alembic может не всегда корректно определять все изменения. Всегда проверяйте автогенерированные миграции перед применением!

### ✅ Рекомендации

1. **Всегда проверяйте миграции** перед применением в production
2. **Тестируйте миграции** на копии production данных
3. **Делайте бэкапы** перед применением миграций
4. **Используйте транзакции** для критических миграций
5. **Документируйте** сложные миграции

### 🔄 Работа с данными

Для миграций, которые изменяют данные (не только структуру), используйте `op.execute()`:

```python
def upgrade() -> None:
    # Изменение структуры
    op.add_column('server_metrics', sa.Column('status', sa.String(50)))
    
    # Изменение данных
    op.execute("""
        UPDATE server_metrics 
        SET status = 'active' 
        WHERE status IS NULL
    """)
```

## Интеграция с CI/CD

### Пример для GitHub Actions

```yaml
- name: Run migrations
  run: |
    alembic -c database/alembic.ini upgrade head
```

### Пример для Docker

```dockerfile
# В Dockerfile
RUN alembic -c database/alembic.ini upgrade head
```

## Troubleshooting

### Проблема: "Target database is not up to date"

**Решение:**
```bash
# Проверьте текущую версию
alembic -c database/alembic.ini current

# Примените все миграции
alembic -c database/alembic.ini upgrade head
```

### Проблема: "Can't locate revision identified by 'xxx'"

**Решение:**
Это означает, что в БД есть версия, которой нет в файлах миграций. Проверьте таблицу `alembic_version` в БД.

### Проблема: Конфликт миграций

**Решение:**
1. Проверьте историю: `alembic -c database/alembic.ini history`
2. Убедитесь, что все миграции применены последовательно
3. При необходимости создайте merge миграцию

## Дополнительные ресурсы

- [Документация Alembic](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Migrations Guide](https://docs.sqlalchemy.org/en/14/core/metadata.html)

