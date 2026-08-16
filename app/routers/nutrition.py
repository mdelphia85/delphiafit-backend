from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database.connection import get_db
from app.utils.security import get_current_user_id

from app.schemas.nutrition import NutritionLogCreate, NutritionLogRead
from app.crud.nutrition import create_nutrition_log, get_nutrition_logs

router = APIRouter(prefix="/nutrition", tags=["nutrition"])

@router.post("/", response_model=NutritionLogRead)
def add_nutrition_log(
    payload: NutritionLogCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return create_nutrition_log(db, user_id, payload)

@router.get("/", response_model=List[NutritionLogRead])
def list_nutrition_logs(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return get_nutrition_logs(db, user_id)
