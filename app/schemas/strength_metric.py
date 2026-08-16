from pydantic import BaseModel
from datetime import datetime

class StrengthMetricBase(BaseModel):
    metric_name: str
    value: float

class StrengthMetricCreate(StrengthMetricBase):
    pass

class StrengthMetricRead(StrengthMetricBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True
