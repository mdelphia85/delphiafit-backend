from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database.connection import get_db
from app.utils.security import get_current_user_id

from app.schemas.rep_logs import RepLogCreate, RepLogRead
from app.crud.rep_logs import create_rep_log, get_rep_logs

router = APIRouter(prefix="/rep-logs", tags=["rep_logs"])

@router.post("/", response_model=RepLogRead)
def add_rep_log(
    payload: RepLogCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return create_rep_log(db, user_id, payload)

@router.get("/", response_model=List[RepLogRead])
def list_rep_logs(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return get_rep_logs(db, user_id)
