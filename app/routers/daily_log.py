from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database.connection import get_db
from app.utils.security import get_current_user_id

from app.schemas.daily_log import DailyLogCreate, DailyLogRead
from app.crud.daily_log import create_daily_log, get_daily_logs

router = APIRouter(prefix="/daily-log", tags=["daily_log"])

@router.post("/", response_model=DailyLogRead)
def add_daily_log(
    payload: DailyLogCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return create_daily_log(db, user_id, payload)

@router.get("/", response_model=List[DailyLogRead])
def list_daily_logs(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return get_daily_logs(db, user_id)
