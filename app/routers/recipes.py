from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database.connection import get_db
from app.utils.security import get_current_user_id

from app.schemas.recipes import RecipeCreate, RecipeRead
from app.crud.recipes import create_recipe, get_recipes

router = APIRouter(prefix="/recipes", tags=["recipes"])

@router.post("/", response_model=RecipeRead)
def add_recipe(
    payload: RecipeCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return create_recipe(db, user_id, payload)

@router.get("/", response_model=List[RecipeRead])
def list_recipes(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return get_recipes(db, user_id)
