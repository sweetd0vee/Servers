from database.connection import Base, engine
from sqlalchemy import Column, DateTime, DECIMAL, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid


class Servers(Base):
    __tablename__ = "servers"

    __table_args__ = (
        UniqueConstraint('vm', 'date', 'metric', name='uq_vm_date_metric'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    vm = Column(String, nullable=False)
    date = Column(DateTime(timezone=True)) # String
    metric = Column(String)
    max_value = Column(DECIMAL(10, 5))
    min_value = Column(DECIMAL(10, 5))
    avg_value = Column(DECIMAL(10, 5))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
