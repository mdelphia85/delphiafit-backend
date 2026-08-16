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

class GoalRead(GoalBase):
    id: int
    user_id: int
    current_value: float
    is_completed: bool
    created_at: datetime

    class Config:
        from_attributes = True
