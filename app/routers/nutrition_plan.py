from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database.connection import get_db
from app.utils.security import get_current_user_id

from app.schemas.nutrition_plan import NutritionPlanCreate, NutritionPlanRead
from app.crud.nutrition_plan import create_nutrition_plan, get_nutrition_plans

router = APIRouter(prefix="/nutrition-plan", tags=["nutrition_plan"])

@router.post("/", response_model=NutritionPlanRead)
def add_nutrition_plan(
    payload: NutritionPlanCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return create_nutrition_plan(db, user_id, payload)

@router.get("/", response_model=List[NutritionPlanRead])
def list_nutrition_plans(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return get_nutrition_plans(db, user_id)
