from pydantic import BaseModel, ConfigDict
from datetime import datetime


class PRRecordBase(BaseModel):
    exercise_name: str
    pr_type: str          # "1RM", "max_reps", "max_weight"
    value: float
    notes: str | None = None


class PRRecordCreate(PRRecordBase):
    pass


class PRRecordUpdate(BaseModel):
    exercise_name: str | None = None
    pr_type: str | None = None
    value: float | None = None
    notes: str | None = None
    is_current: bool | None = None


class PRRecordRead(PRRecordBase):
    id: int
    user_id: int
    is_current: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
