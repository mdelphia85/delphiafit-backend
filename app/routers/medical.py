from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

from app.database.connection import get_db
from app.crud.medical import MedicalCRUD

router = APIRouter(prefix="/medical", tags=["Medical"])
crud = MedicalCRUD()


# ---------------------------------------------------------
# Request Models
# ---------------------------------------------------------

class InjuryCreate(BaseModel):
    user_id: int
    type: str
    severity: str
    description: Optional[str] = None
    occurred_at: datetime


class PTCreate(BaseModel):
    injury_id: int
    name: str
    description: Optional[str] = None
    frequency_per_week: Optional[int] = 3
    duration_weeks: Optional[int] = 4


class RecoveryCreate(BaseModel):
    injury_id: int
    name: str
    description: Optional[str] = None


# ---------------------------------------------------------
# Injury Logging
# ---------------------------------------------------------
@router.post("/injury/log")
def log_injury(data: InjuryCreate, db: Session = Depends(get_db)):
    try:
        return crud.log_injury(db, data.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/injury/{injury_id}")
def get_injury(injury_id: int, db: Session = Depends(get_db)):
    injury = crud.get_injury(db, injury_id)
    if not injury:
        raise HTTPException(status_code=404, detail="Injury not found.")
    return injury


@router.get("/injury/user/{user_id}")
def list_injuries(user_id: int, db: Session = Depends(get_db)):
    return crud.list_injuries(db, user_id)


@router.post("/injury/{injury_id}/resolve")
def resolve_injury(injury_id: int, db: Session = Depends(get_db)):
    try:
        return crud.resolve_injury(db, injury_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# PT Plans
# ---------------------------------------------------------
@router.post("/pt/create")
def create_pt_plan(data: PTCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_pt_plan(db, data.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/pt/injury/{injury_id}")
def list_pt_plans(injury_id: int, db: Session = Depends(get_db)):
    return crud.list_pt_plans(db, injury_id)


# ---------------------------------------------------------
# Recovery Protocols
# ---------------------------------------------------------
@router.post("/recovery/create")
def create_recovery_protocol(data: RecoveryCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_recovery_protocol(db, data.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/recovery/injury/{injury_id}")
def list_recovery_protocols(injury_id: int, db: Session = Depends(get_db)):
    return crud.list_recovery_protocols(db, injury_id)
