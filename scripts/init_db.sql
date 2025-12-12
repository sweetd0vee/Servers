-- Создание таблицы servers

CREATE TABLE IF NOT EXISTS servers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vm VARCHAR(255) NOT NULL,
    date TIMESTAMP WITH TIME ZONE NOT NULL,
    metric VARCHAR(100) NOT NULL,
    max_value DECIMAL(20, 5),
    min_value DECIMAL(20, 5),
    avg_value DECIMAL(20, 5),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Уникальное ограничение
    CONSTRAINT uq_vm_date_metric UNIQUE (vm, date, metric)
);

-- Создание индексов для оптимизации запросов
CREATE INDEX IF NOT EXISTS idx_servers_id ON servers(id);
CREATE INDEX IF NOT EXISTS idx_servers_vm ON servers(vm);
CREATE INDEX IF NOT EXISTS idx_servers_date ON servers(date);
CREATE INDEX IF NOT EXISTS idx_servers_metric ON servers(metric);
CREATE INDEX IF NOT EXISTS idx_servers_created_at ON servers(created_at);

-- Композитные индексы для часто используемых запросов
CREATE INDEX IF NOT EXISTS idx_servers_vm_date ON servers(vm, date);
CREATE INDEX IF NOT EXISTS idx_servers_metric_date ON servers(metric, date);
CREATE INDEX IF NOT EXISTS idx_servers_vm_metric ON servers(vm, metric);

-- Комментарии к таблице и колонкам
COMMENT ON TABLE servers IS 'Метрики производительности серверов';
COMMENT ON COLUMN servers.id IS 'Уникальный идентификатор записи';
COMMENT ON COLUMN servers.vm IS 'Имя виртуальной машины';
COMMENT ON COLUMN servers.date IS 'Дата и время сбора метрики';
COMMENT ON COLUMN servers.metric IS 'Название метрики (например: cpu.usage.average)';
COMMENT ON COLUMN servers.max_value IS 'Максимальное значение метрики за период';
COMMENT ON COLUMN servers.min_value IS 'Минимальное значение метрики за период';
COMMENT ON COLUMN servers.avg_value IS 'Среднее значение метрики за период';
COMMENT ON COLUMN servers.created_at IS 'Дата создания записи в базе данных';