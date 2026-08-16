from pydantic import BaseModel
from datetime import datetime

class HydrationLogBase(BaseModel):
    amount_ml: int
    date: datetime
    notes: str | None = None

class HydrationLogCreate(HydrationLogBase):
    user_id: int

class HydrationLogRead(HydrationLogBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
