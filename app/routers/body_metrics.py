from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database.connection import get_db
from app.utils.security import get_current_user_id

from app.schemas.body_metrics import BodyMetricCreate, BodyMetricRead
from app.crud.body_metrics import create_body_metric, get_body_metrics

router = APIRouter(prefix="/body-metrics", tags=["body_metrics"])

@router.post("/", response_model=BodyMetricRead)
def add_body_metric(
    payload: BodyMetricCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return create_body_metric(db, user_id, payload)

@router.get("/", response_model=List[BodyMetricRead])
def list_body_metrics(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return get_body_metrics(db, user_id)
