from pydantic import BaseModel
from datetime import datetime


class ActivityLogBase(BaseModel):
    activity_type: str
    duration_minutes: int
    calories_burned: int | None = None
    notes: str | None = None
    date: datetime


class ActivityLogCreate(ActivityLogBase):
    user_id: int


class ActivityLogUpdate(BaseModel):
    activity_type: str | None = None
    duration_minutes: int | None = None
    calories_burned: int | None = None
    notes: str | None = None
    date: datetime | None = None


class ActivityLogRead(ActivityLogBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
