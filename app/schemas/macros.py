from pydantic import BaseModel
from datetime import datetime

class MacroPlanBase(BaseModel):
    daily_calories: int
    daily_protein: int
    daily_carbs: int
    daily_fats: int

class MacroPlanCreate(MacroPlanBase):
    pass

class MacroPlanRead(MacroPlanBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True
