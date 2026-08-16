from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database.connection import get_db
from app.utils.security import get_current_user_id

from app.schemas.activity import ActivityLogCreate, ActivityLogRead
from app.crud.activity import create_activity_log, get_activity_logs

router = APIRouter(prefix="/activity", tags=["activity"])

@router.post("/", response_model=ActivityLogRead)
def add_activity_log(
    payload: ActivityLogCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return create_activity_log(db, user_id, payload)

@router.get("/", response_model=List[ActivityLogRead])
def list_activity_logs(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return get_activity_logs(db, user_id)
