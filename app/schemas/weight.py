from pydantic import BaseModel
from datetime import datetime

class WeightLogCreate(BaseModel):
    user_id: int
    weight: float
    body_fat: float | None = None
    date: datetime

class WeightLogRead(BaseModel):
    id: int
    user_id: int
    weight: float
    body_fat: float | None = None
    date: datetime

    class Config:
        orm_mode = True
