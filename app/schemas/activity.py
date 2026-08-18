from pydantic import BaseModel, ConfigDict
from datetime import datetime


class ActivityLogBase(BaseModel):
    activity_type: str
    duration_minutes: int
    calories_burned: int | None = None
    notes: str | None = None
    date: datetime


class ActivityLogCreate(ActivityLogBase):
    pass


class ActivityLogUpdate(BaseModel):
    activity_type: str | None = None
    duration_minutes: int | None = None
    calories_burned: int | None = None
    notes: str | None = None
    date: datetime | None = None


class ActivityLogRead(ActivityLogBase):
    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)
