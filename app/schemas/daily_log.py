from pydantic import BaseModel
from datetime import datetime

class DailyLogBase(BaseModel):
    date: datetime
    mood: str | None = None
    energy_level: int | None = None
    notes: str | None = None


class DailyLogCreate(DailyLogBase):
    user_id: int


class DailyLogUpdate(BaseModel):
    date: datetime | None = None
    mood: str | None = None
    energy_level: int | None = None
    notes: str | None = None


class DailyLogRead(DailyLogBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
