from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class NutritionLogBase(BaseModel):
    calories: int
    protein: int
    carbs: int
    fats: int
    water_oz: int
    notes: Optional[str] = None

class NutritionLogCreate(NutritionLogBase):
    pass

class NutritionLogRead(NutritionLogBase):
    id: int
    user_id: int
    recorded_at: datetime

    class Config:
        from_attributes = True
