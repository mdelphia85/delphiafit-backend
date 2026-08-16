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


class NutritionLogUpdate(BaseModel):
    calories: Optional[int] = None
    protein: Optional[int] = None
    carbs: Optional[int] = None
    fats: Optional[int] = None
    water_oz: Optional[int] = None
    notes: Optional[str] = None


class NutritionLogRead(NutritionLogBase):
    id: int
    user_id: int
    recorded_at: datetime

    class Config:
        from_attributes = True
