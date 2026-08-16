from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database.connection import get_db
from app.utils.security import get_current_user_id

from app.schemas.weight import WeightLogCreate, WeightLogRead
from app.crud.weight import create_weight_log, get_weight_logs

router = APIRouter(prefix="/weight", tags=["weight"])

@router.post("/", response_model=WeightLogRead)
def add_weight_log(
    payload: WeightLogCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return create_weight_log(db, user_id, payload)

@router.get("/", response_model=List[WeightLogRead])
def list_weight_logs(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return get_weight_logs(db, user_id)
