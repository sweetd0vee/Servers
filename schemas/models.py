from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, validator


class HealthResponse(BaseModel):
    status: str


class ServerMetrics(BaseModel):
    id: UUID
    date: datetime
    vm: str = Field(..., min_length=1, max_length=100)
    metric: str = Field(..., min_length=1, max_length=100)
    max_value: Decimal = Field(..., ge=0, max_digits=10, decimal_places=5)
    min_value: Decimal = Field(..., ge=0, max_digits=10, decimal_places=5)
    avg_value: Decimal = Field(..., ge=0, max_digits=10, decimal_places=5)
    created_at: datetime

    class Config:
        orm_mode = True