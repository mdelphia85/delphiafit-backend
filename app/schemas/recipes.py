from pydantic import BaseModel
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

class RecipeRead(RecipeBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True
