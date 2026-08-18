from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class NutritionLogCreate(BaseModel):
    calories: int = 0
    protein: int = 0
    carbs: int = 0
    fats: int = 0
    water_oz: int = 0
    notes: Optional[str] = None


class NutritionLogUpdate(BaseModel):
    calories: Optional[int] = None
    protein: Optional[int] = None
    carbs: Optional[int] = None
    fats: Optional[int] = None
    water_oz: Optional[int] = None
    notes: Optional[str] = None


class NutritionLogRead(BaseModel):
    id: int
    user_id: int

    calories: int
    protein: int
    carbs: int
    fats: int
    water_oz: int

    notes: Optional[str] = None
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)