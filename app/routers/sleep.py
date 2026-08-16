from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database.connection import get_db
from app.utils.security import get_current_user_id

from app.schemas.sleep import SleepLogCreate, SleepLogRead
from app.crud.sleep import create_sleep_log, get_sleep_logs

router = APIRouter(prefix="/sleep", tags=["sleep"])

@router.post("/", response_model=SleepLogRead)
def add_sleep_log(
    payload: SleepLogCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return create_sleep_log(db, user_id, payload)

@router.get("/", response_model=List[SleepLogRead])
def list_sleep_logs(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return get_sleep_logs(db, user_id)
