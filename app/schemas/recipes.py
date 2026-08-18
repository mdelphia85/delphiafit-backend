from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Dict


class RecipeBase(BaseModel):
    name: str
    ingredients: List[Dict[str, str]]
    instructions: str
    calories: int
    protein: int
    carbs: int
    fats: int


class RecipeCreate(RecipeBase):
    pass


class RecipeUpdate(BaseModel):
    name: str | None = None
    ingredients: List[Dict[str, str]] | None = None
    instructions: str | None = None
    calories: int | None = None
    protein: int | None = None
    carbs: int | None = None
    fats: int | None = None


class RecipeRead(RecipeBase):
    id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
