from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class GoalBase(BaseModel):
    title: str
    target_metric: str
    target_value: float
    deadline: Optional[datetime] = None


class GoalCreate(GoalBase):
    pass


class GoalUpdate(BaseModel):
    title: Optional[str] = None
    target_metric: Optional[str] = None
    target_value: Optional[float] = None
    deadline: Optional[datetime] = None
    current_value: Optional[float] = None
    is_completed: Optional[bool] = None


class GoalRead(GoalBase):
    id: int
    user_id: int
    current_value: float
    is_completed: bool
    created_at: datetime

    class Config:
        from_attributes = True
