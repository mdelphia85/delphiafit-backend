from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.database.connection import get_db
from app.crud.medical_recovery import MedicalRecoveryCRUD

router = APIRouter(prefix="/medical/recovery", tags=["medical-recovery"])
crud = MedicalRecoveryCRUD()


# ---------------------------------------------------------
# Schemas
# ---------------------------------------------------------

class ProtocolCreate(BaseModel):
    injury_id: int
    name: str
    description: Optional[str] = None


class StageCreate(BaseModel):
    protocol_id: int
    name: str
    instructions: Optional[str] = None
    objective_criteria: Optional[str] = None
    order_index: int


class ProgressUpdate(BaseModel):
    stage_id: int
    user_id: int
    completed: bool
    clinician_notes: Optional[str] = None


class ClearanceUpdate(BaseModel):
    injury_id: int
    user_id: int
    clinician_id: Optional[int] = None
    cleared: bool
    notes: Optional[str] = None


# ---------------------------------------------------------
# Protocol
# ---------------------------------------------------------
@router.post("/protocol")
def create_protocol(data: ProtocolCreate, db: Session = Depends(get_db)):
    return crud.create_protocol(db, data.dict())


@router.get("/protocol/{injury_id}")
def list_protocols(injury_id: int, db: Session = Depends(get_db)):
    return crud.list_protocols(db, injury_id)


# ---------------------------------------------------------
# Stages
# ---------------------------------------------------------
@router.post("/stage")
def add_stage(data: StageCreate, db: Session = Depends(get_db)):
    return crud.add_stage(db, data.dict())


@router.get("/stage/{protocol_id}")
def list_stages(protocol_id: int, db: Session = Depends(get_db)):
    return crud.list_stages(db, protocol_id)


# ---------------------------------------------------------
# Progress
# ---------------------------------------------------------
@router.post("/progress")
def update_progress(data: ProgressUpdate, db: Session = Depends(get_db)):
    return crud.update_progress(db, data.dict())


@router.get("/progress/{stage_id}/{user_id}")
def get_progress(stage_id: int, user_id: int, db: Session = Depends(get_db)):
    return crud.get_progress(db, stage_id, user_id)


# ---------------------------------------------------------
# Clearance
# ---------------------------------------------------------
@router.post("/clearance")
def set_clearance(data: ClearanceUpdate, db: Session = Depends(get_db)):
    return crud.set_clearance(db, data.dict())


@router.get("/clearance/{injury_id}/{user_id}")
def get_clearance(injury_id: int, user_id: int, db: Session = Depends(get_db)):
    return crud.get_clearance(db, injury_id, user_id)
