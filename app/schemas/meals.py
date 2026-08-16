from pydantic import BaseModel
from datetime import datetime

class MealBase(BaseModel):
    name: str
    calories: int
    protein: int
    carbs: int
    fats: int

class MealCreate(MealBase):
    pass

class MealRead(MealBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True
