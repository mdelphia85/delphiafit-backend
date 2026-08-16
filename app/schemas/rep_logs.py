from pydantic import BaseModel
from datetime import datetime

class RepLogBase(BaseModel):
    exercise_name: str
    reps: int
    weight: float

class RepLogCreate(RepLogBase):
    pass

class RepLogRead(RepLogBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True
