from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database.connection import get_db
from app.crud.unit import UnitCRUD
from app.services.unit_engine import UnitEngine

router = APIRouter(prefix="/unit", tags=["Unit Builder"])
crud = UnitCRUD()
engine = UnitEngine()


# ---------------------------------------------------------
# Schemas
# ---------------------------------------------------------

class UnitCreate(BaseModel):
    name: str
    unit_type: str
    description: Optional[str] = None


class MemberCreate(BaseModel):
    unit_id: int
    user_id: int
    role: str
    notes: Optional[str] = None


class CapabilityCreate(BaseModel):
    unit_id: int
    capability: str
    score: Optional[float] = 0.0
    notes: Optional[str] = None


# ---------------------------------------------------------
# Units
# ---------------------------------------------------------
@router.post("/create")
def create_unit(data: UnitCreate, db: Session = Depends(get_db)):
    return crud.create_unit(db, data.dict())


@router.get("/list")
def list_units(db: Session = Depends(get_db)):
    return crud.list_units(db)


@router.get("/{unit_id}")
def get_unit(unit_id: int, db: Session = Depends(get_db)):
    unit = crud.get_unit(db, unit_id)
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found.")
    return unit


# ---------------------------------------------------------
# Members
# ---------------------------------------------------------
@router.post("/member")
def add_member(data: MemberCreate, db: Session = Depends(get_db)):
    return crud.add_member(db, data.dict())


@router.get("/member/{unit_id}")
def list_members(unit_id: int, db: Session = Depends(get_db)):
    return crud.list_members(db, unit_id)


# ---------------------------------------------------------
# Capabilities
# ---------------------------------------------------------
@router.post("/capability")
def add_capability(data: CapabilityCreate, db: Session = Depends(get_db)):
    return crud.add_capability(db, data.dict())


@router.get("/capability/{unit_id}")
def list_capabilities(unit_id: int, db: Session = Depends(get_db)):
    return crud.list_capabilities(db, unit_id)


# ---------------------------------------------------------
# Readiness
# ---------------------------------------------------------
@router.post("/{unit_id}/readiness")
def update_readiness(unit_id: int, db: Session = Depends(get_db)):
    members = crud.list_members(db, unit_id)
    capabilities = crud.list_capabilities(db, unit_id)

    readiness = engine.compute_readiness(members, capabilities)

    return crud.update_readiness(db, unit_id, readiness["readiness_score"])
