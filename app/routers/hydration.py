from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database.connection import get_db
from app.utils.security import get_current_user_id

from app.schemas.hydration import HydrationLogCreate, HydrationLogRead
from app.crud.hydration import create_hydration_log, get_hydration_logs

router = APIRouter(prefix="/hydration", tags=["hydration"])

@router.post("/", response_model=HydrationLogRead)
def add_hydration_log(
    payload: HydrationLogCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return create_hydration_log(db, user_id, payload)

@router.get("/", response_model=List[HydrationLogRead])
def list_hydration_logs(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return get_hydration_logs(db, user_id)
