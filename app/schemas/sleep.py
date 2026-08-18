from pydantic import BaseModel, ConfigDict
from datetime import datetime


class SleepLogBase(BaseModel):
    duration_hours: float
    quality: int | None = None  # 1–10 scale
    notes: str | None = None
    date: datetime


class SleepLogCreate(SleepLogBase):
    pass


class SleepLogUpdate(BaseModel):
    duration_hours: float | None = None
    quality: int | None = None
    notes: str | None = None
    date: datetime | None = None


class SleepLogRead(SleepLogBase):
    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)
