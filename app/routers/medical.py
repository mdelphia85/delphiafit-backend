from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.crud.medical import MedicalCRUD
from app.models.injury import Injury
from app.utils.security import get_current_user_id

router = APIRouter(prefix="/medical", tags=["Medical"])
crud = MedicalCRUD()


class InjuryCreate(BaseModel):
    type: str
    severity: str
    description: Optional[str] = None
    occurred_at: datetime


class PTCreate(BaseModel):
    injury_id: int
    name: str
    description: Optional[str] = None
    frequency_per_week: Optional[int] = Field(default=3, ge=1, le=14)
    duration_weeks: Optional[int] = Field(default=4, ge=1, le=52)


class RecoveryCreate(BaseModel):
    injury_id: int
    name: str
    description: Optional[str] = None


def _owned_injury(db: Session, injury_id: int, user_id: int):
    injury = db.query(Injury).filter(Injury.id == injury_id, Injury.user_id == user_id).first()
    if injury is None:
        raise HTTPException(status_code=404, detail="Injury not found.")
    return injury


@router.post("/injury/log")
def log_injury(data: InjuryCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return crud.log_injury(db, {**data.model_dump(), "user_id": user_id})


@router.get("/injury/me")
def list_my_injuries(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return crud.list_injuries(db, user_id)


@router.get("/injury/{injury_id}")
def get_injury(injury_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return _owned_injury(db, injury_id, user_id)


@router.get("/injury/user/{user_id}")
def list_injuries(user_id: int, current_user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    if user_id != current_user_id:
        raise HTTPException(status_code=404, detail="Injuries not found.")
    return crud.list_injuries(db, current_user_id)


@router.post("/injury/{injury_id}/resolve")
def resolve_injury(injury_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    _owned_injury(db, injury_id, user_id)
    return crud.resolve_injury(db, injury_id)


@router.post("/pt/create")
def create_pt_plan(data: PTCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    _owned_injury(db, data.injury_id, user_id)
    return crud.create_pt_plan(db, data.model_dump())


@router.get("/pt/injury/{injury_id}")
def list_pt_plans(injury_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    _owned_injury(db, injury_id, user_id)
    return crud.list_pt_plans(db, injury_id)


@router.post("/recovery/create")
def create_recovery_protocol(data: RecoveryCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    _owned_injury(db, data.injury_id, user_id)
    return crud.create_recovery_protocol(db, data.model_dump())


@router.get("/recovery/injury/{injury_id}")
def list_recovery_protocols(injury_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    _owned_injury(db, injury_id, user_id)
    return crud.list_recovery_protocols(db, injury_id)
