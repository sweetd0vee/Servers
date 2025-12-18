from database.connection import Base, engine
from sqlalchemy import Column, DateTime, DECIMAL, String, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid


class ServerMetrics(Base):
    """
    Модель для хранения метрик серверов
    Соответствующая таблице server_metrics в PostgreSQL
    """
    __tablename__ = "server_metrics"

    __table_args__ = (
        UniqueConstraint('vm', 'date', 'metric', name='uq_vm_date_metric'),
        Index('idx_metrics_vm_date', 'vm', 'date', 'metric'),
        Index('idx_metrics_date', 'date'),
        Index('idx_metrics_metric', 'metric'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    vm = Column(String(255), nullable=False, index=True)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    metric = Column(String(100), nullable=False, index=True)
    max_value = Column(DECIMAL(20, 5), nullable=True)
    min_value = Column(DECIMAL(20, 5), nullable=True)
    avg_value = Column(DECIMAL(20, 5), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<ServerMetrics(vm='{self.vm}', date='{self.date}', metric='{self.metric}', avg_value={self.avg_value})>"


class VMMetrics(Base):
    """
    Сырые метрики виртуальных машин из vCenter
    """
    __tablename__ = "vm_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vm_name = Column(String(255), nullable=False, index=True)
    vcenter = Column(String(100), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)

    # CPU метрики
    cpu_usage_average = Column(DECIMAL(20, 5), nullable=True)  # cpu.usage.average, %
    cpu_ready_summation = Column(DECIMAL(20, 5), nullable=True)  # cpu.ready.summation, milliseconds
    cpu_usagemhz_average = Column(DECIMAL(20, 5), nullable=True)  # cpu.usagemhz.average, MHz

    # Memory метрики
    mem_usage_average = Column(DECIMAL(20, 5), nullable=True)  # mem.usage.average, %
    mem_consumed_average = Column(DECIMAL(20, 5), nullable=True)  # mem.consumed.average, Kbs
    mem_vmmemctl_average = Column(DECIMAL(20, 5), nullable=True)  # mem.vmmemctl.average, Kbs

    # Disk метрики
    disk_usage_average = Column(DECIMAL(20, 5), nullable=True)  # disk.usage.average, Kbps
    disk_maxtotallatency_latest = Column(DECIMAL(20, 5), nullable=True)  # disk.maxtotallatency.latest, milliseconds

    # Network метрики
    net_usage_average = Column(DECIMAL(20, 5), nullable=True)  # net.usage.average, Kbps

    # Метаданные
    # is_anomaly = Column(Boolean, default=False, index=True)
    # anomaly_score = Column(Float, nullable=True)
    # tags = Column(JSONB, default=dict)  # Дополнительные теги (например, environment, business_unit)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_vm_metrics_vm_timestamp', 'vm_name', 'timestamp'),
        Index('idx_vm_metrics_vcenter_timestamp', 'vcenter', 'timestamp'),
    )


Base.metadata.create_all(engine)
