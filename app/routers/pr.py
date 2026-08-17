from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database.connection import get_db
from app.schemas.pr_records import PRRecordCreate, PRRecordRead
from app.crud.pr_records import create_pr, get_prs
from app.utils.security import get_current_user_id

router = APIRouter(prefix="/prs", tags=["personal_records"])

@router.post("/", response_model=PRRecordRead)
def add_pr(
    payload: PRRecordCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return create_pr(db, user_id, payload)

@router.get("/", response_model=List[PRRecordRead])
def list_prs(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return get_prs(db, user_id)
