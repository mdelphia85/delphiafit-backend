from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database.connection import get_db
from app.utils.security import get_current_user_id

from app.schemas.sports_performance import (
    SportsPerformanceCreate,
    SportsPerformanceRead
)
from app.crud.sports_performance import (
    create_sports_performance,
    get_sports_performances
)

router = APIRouter(prefix="/sports-performance", tags=["sports_performance"])

@router.post("/", response_model=SportsPerformanceRead)
def add_sports_performance(
    payload: SportsPerformanceCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return create_sports_performance(db, user_id, payload)

@router.get("/", response_model=List[SportsPerformanceRead])
def list_sports_performances(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return get_sports_performances(db, user_id)
