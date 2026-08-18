from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database.connection import get_db
from app.utils.security import get_current_user_id

from app.schemas.sports_log import (
    SportsLogCreate,
    SportsLogRead
)
from app.crud.sports_log import (
    create_sports_log,
    get_sports_logs
)

router = APIRouter(prefix="/sports/logs", tags=["sports logs"])

@router.post("/", response_model=SportsLogRead)
def add_sports_log(
    payload: SportsLogCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return create_sports_log(db, user_id, payload)

@router.get("/", response_model=List[SportsLogRead])
def list_sports_logs(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return get_sports_logs(db, user_id)
