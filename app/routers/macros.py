from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database.connection import get_db
from app.utils.security import get_current_user_id

from app.schemas.macros import MacroPlanCreate, MacroPlanRead
from app.crud.macros import create_macro_plan, get_macro_plans

router = APIRouter(prefix="/macros", tags=["macros"])

@router.post("/", response_model=MacroPlanRead)
def add_macro_plan(
    payload: MacroPlanCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return create_macro_plan(db, user_id, payload)

@router.get("/", response_model=List[MacroPlanRead])
def list_macro_plans(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return get_macro_plans(db, user_id)
