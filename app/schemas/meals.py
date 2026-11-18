from datetime import datetime
from pydantic import BaseModel, ConfigDict


class MealBase(BaseModel):
    name: str
    calories: int = 0
    protein: int = 0
    carbs: int = 0
    fats: int = 0


class MealCreate(MealBase):
    pass


class MealUpdate(BaseModel):
    name: str | None = None
    calories: int | None = None
    protein: int | None = None
    carbs: int | None = None
    fats: int | None = None


class MealRead(MealBase):
    id: int
    user_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
