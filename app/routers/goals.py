from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database.connection import get_db
from app.utils.security import get_current_user_id

from app.schemas.goals import GoalCreate, GoalRead
from app.crud.goals import create_goal, get_goals

router = APIRouter(prefix="/goals", tags=["goals"])

@router.post("/", response_model=GoalRead)
def add_goal(
    payload: GoalCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return create_goal(db, user_id, payload)

@router.get("/", response_model=List[GoalRead])
def list_goals(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return get_goals(db, user_id)
