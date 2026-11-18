from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.crud.medical_recovery import MedicalRecoveryCRUD
from app.models.injury import Injury
from app.models.recovery_protocol import RecoveryProtocol
from app.models.recovery_stage import RecoveryStage
from app.utils.security import get_current_user_id

router = APIRouter(prefix="/medical/recovery", tags=["medical-recovery"])
crud = MedicalRecoveryCRUD()


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
    completed: bool
    clinician_notes: Optional[str] = None


class ClearanceUpdate(BaseModel):
    injury_id: int
    cleared: bool
    notes: Optional[str] = None


def _injury(db: Session, injury_id: int, user_id: int):
    row = db.query(Injury).filter_by(id=injury_id, user_id=user_id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Injury not found.")
    return row


def _protocol(db: Session, protocol_id: int, user_id: int):
    row = db.query(RecoveryProtocol).filter_by(id=protocol_id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Recovery protocol not found.")
    _injury(db, row.injury_id, user_id)
    return row


def _stage(db: Session, stage_id: int, user_id: int):
    row = db.query(RecoveryStage).filter_by(id=stage_id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Recovery stage not found.")
    _protocol(db, row.protocol_id, user_id)
    return row


@router.post("/protocol")
def create_protocol(data: ProtocolCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    _injury(db, data.injury_id, user_id)
    return crud.create_protocol(db, data.model_dump())


@router.get("/protocol/{injury_id}")
def list_protocols(injury_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    _injury(db, injury_id, user_id)
    return crud.list_protocols(db, injury_id)


@router.post("/stage")
def add_stage(data: StageCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    _protocol(db, data.protocol_id, user_id)
    return crud.add_stage(db, data.model_dump())


@router.get("/stage/{protocol_id}")
def list_stages(protocol_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    _protocol(db, protocol_id, user_id)
    return crud.list_stages(db, protocol_id)


@router.post("/progress")
def update_progress(data: ProgressUpdate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    _stage(db, data.stage_id, user_id)
    return crud.update_progress(db, {**data.model_dump(), "user_id": user_id})


@router.get("/progress/{stage_id}/{user_id}")
def get_progress(stage_id: int, user_id: int, current_user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    if user_id != current_user_id:
        raise HTTPException(status_code=404, detail="Recovery progress not found.")
    _stage(db, stage_id, current_user_id)
    return crud.get_progress(db, stage_id, current_user_id)


@router.post("/clearance")
def set_clearance(data: ClearanceUpdate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    _injury(db, data.injury_id, user_id)
    return crud.set_clearance(db, {**data.model_dump(), "user_id": user_id, "clinician_id": None})


@router.get("/clearance/{injury_id}/me")
def get_my_clearance(injury_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    _injury(db, injury_id, user_id)
    return crud.get_clearance(db, injury_id, user_id)


@router.get("/clearance/{injury_id}/{user_id}")
def get_clearance(injury_id: int, user_id: int, current_user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    if user_id != current_user_id:
        raise HTTPException(status_code=404, detail="Clearance not found.")
    _injury(db, injury_id, current_user_id)
    return crud.get_clearance(db, injury_id, current_user_id)
