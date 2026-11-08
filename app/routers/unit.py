from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.crud.unit import UnitCRUD
from app.models.unit import Unit, UnitMember
from app.models.user import User
from app.services.unit_engine import UnitEngine
from app.utils.security import get_current_user_id

router = APIRouter(prefix="/unit", tags=["Unit Builder"])
crud = UnitCRUD()
engine = UnitEngine()


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


def unit_payload(unit: Unit):
    return {
        "id": unit.id,
        "name": unit.name,
        "unit_type": unit.unit_type,
        "description": unit.description,
        "readiness_score": unit.readiness_score,
        "active": unit.active,
        "created_at": unit.created_at,
        "updated_at": unit.updated_at,
    }


def require_unit(db: Session, unit_id: int, user_id: int, *, owner_only: bool = False):
    query = db.query(Unit).filter(Unit.id == unit_id, Unit.active.is_(True))
    if owner_only:
        query = query.filter(Unit.owner_user_id == user_id)
    else:
        query = query.outerjoin(UnitMember, UnitMember.unit_id == Unit.id).filter(
            (Unit.owner_user_id == user_id) | (UnitMember.user_id == user_id)
        )
    unit = query.first()
    if unit is None:
        raise HTTPException(status_code=404, detail="Unit not found.")
    return unit


@router.post("/create")
def create_unit(data: UnitCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    unit = crud.create_unit(db, {**data.model_dump(), "owner_user_id": user_id})
    return unit_payload(unit)


@router.get("/list")
def list_units(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return [unit_payload(unit) for unit in crud.list_units(db, user_id)]


@router.get("/{unit_id}")
def get_unit(unit_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    unit = require_unit(db, unit_id, user_id)
    return unit_payload(unit)


@router.post("/member")
def add_member(data: MemberCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    require_unit(db, data.unit_id, user_id, owner_only=True)
    if db.query(User.id).filter(User.id == data.user_id).first() is None:
        raise HTTPException(status_code=404, detail="User not found.")
    return crud.add_member(db, data.model_dump())


@router.get("/member/{unit_id}")
def list_members(unit_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    require_unit(db, unit_id, user_id)
    return crud.list_members(db, unit_id)


@router.post("/capability")
def add_capability(data: CapabilityCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    require_unit(db, data.unit_id, user_id, owner_only=True)
    return crud.add_capability(db, data.model_dump())


@router.get("/capability/{unit_id}")
def list_capabilities(unit_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    require_unit(db, unit_id, user_id)
    return crud.list_capabilities(db, unit_id)


@router.post("/{unit_id}/readiness")
def update_readiness(unit_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    require_unit(db, unit_id, user_id, owner_only=True)
    members = crud.list_members(db, unit_id)
    capabilities = crud.list_capabilities(db, unit_id)
    readiness = engine.compute_readiness(members, capabilities)
    return unit_payload(crud.update_readiness(db, unit_id, readiness["readiness_score"]))
