from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database.connection import get_db
from app.utils.security import get_current_user_id

from app.schemas.recovery import RecoveryCreate, RecoveryRead
from app.crud.recovery import create_recovery_log, get_recovery_logs

router = APIRouter(prefix="/recovery", tags=["recovery"])

@router.post("/", response_model=RecoveryRead)
def add_recovery_log(
    payload: RecoveryCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return create_recovery_log(db, user_id, payload)

@router.get("/", response_model=List[RecoveryRead])
def list_recovery_logs(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return get_recovery_logs(db, user_id)
