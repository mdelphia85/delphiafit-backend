from pydantic import BaseModel
from datetime import datetime

class SleepLogBase(BaseModel):
    duration_hours: float
    quality: int | None = None  # 1–10 scale
    notes: str | None = None
    date: datetime

class SleepLogCreate(SleepLogBase):
    user_id: int

class SleepLogRead(SleepLogBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
