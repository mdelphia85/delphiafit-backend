from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database.connection import get_db
from app.schemas.strength_metric import StrengthMetricCreate, StrengthMetricRead
from app.crud.strength_metric import create_strength_metric, get_strength_metrics
from app.utils.security import get_current_user_id

router = APIRouter(prefix="/strength", tags=["strength"])

@router.post("/", response_model=StrengthMetricRead)
def add_strength_metric(
    payload: StrengthMetricCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return create_strength_metric(db, user_id, payload)

@router.get("/", response_model=List[StrengthMetricRead])
def list_strength_metrics(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return get_strength_metrics(db, user_id)
