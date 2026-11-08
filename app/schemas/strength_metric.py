from pydantic import BaseModel, ConfigDict
from datetime import datetime


class StrengthMetricBase(BaseModel):
    metric_name: str
    value: float


class StrengthMetricCreate(StrengthMetricBase):
    pass


class StrengthMetricUpdate(BaseModel):
    metric_name: str | None = None
    value: float | None = None
    created_at: datetime | None = None


class StrengthMetricRead(StrengthMetricBase):
    id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
