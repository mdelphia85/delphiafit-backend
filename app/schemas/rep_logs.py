from pydantic import BaseModel, ConfigDict
from datetime import datetime


class RepLogBase(BaseModel):
    exercise_name: str
    reps: int
    weight: float


class RepLogCreate(RepLogBase):
    pass


class RepLogUpdate(BaseModel):
    exercise_name: str | None = None
    reps: int | None = None
    weight: float | None = None
    created_at: datetime | None = None


class RepLogRead(RepLogBase):
    id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
