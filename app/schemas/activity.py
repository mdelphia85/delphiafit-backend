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

class ActivityLogRead(ActivityLogBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
