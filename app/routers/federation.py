from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.database.connection import get_db
from app.crud.federation import FederationCRUD
from app.models.federation import Federation
from app.models.community_area import FederationMembership
from app.models.user import User
from app.utils.security import get_current_user_id

router = APIRouter(prefix="/federation", tags=["Federation"])
crud = FederationCRUD()


# ---------------------------------------------------------
# Request Models
# ---------------------------------------------------------

class FederationCreate(BaseModel):
    name: str
    country: Optional[str] = None
    sport: Optional[str] = None
    rulebook: Optional[str] = None
    licensing_requirements: Optional[str] = None


class FederationUpdate(BaseModel):
    updates: Dict[str, Any]


class RulebookUpdate(BaseModel):
    rulebook: str


class LicensingUpdate(BaseModel):
    licensing_requirements: str


# ---------------------------------------------------------
# Create Federation
# ---------------------------------------------------------
@router.post("/create")
def create_federation(data: FederationCreate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    try:
        federation = crud.create_federation(db, data.model_dump())
        db.add(FederationMembership(federation_id=federation.id, user_id=user_id, role="owner"))
        db.commit()
        db.refresh(federation)
        return federation
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Get Federation by ID
# ---------------------------------------------------------
@router.get("/{federation_id:int}")
def get_federation(federation_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    fed = crud.get_federation(db, federation_id)
    if not fed:
        raise HTTPException(status_code=404, detail="Federation not found.")
    _require_member(db, fed.id, user_id)
    return fed


# ---------------------------------------------------------
# List Federations
# ---------------------------------------------------------
@router.get("/list")
def list_federations(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    memberships = {row.federation_id for row in db.query(FederationMembership).filter_by(user_id=user_id).all()}
    return [{"id": fed.id, "name": fed.name, "country": fed.country, "sport": fed.sport,
             "joined": fed.id in memberships} for fed in crud.list_federations(db)]


# ---------------------------------------------------------
# Update Federation
# ---------------------------------------------------------
@router.put("/{federation_id}/update")
def update_federation(federation_id: int, data: FederationUpdate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    _require_owner(db, federation_id, user_id)
    try:
        return crud.update_federation(db, federation_id, {key: value for key, value in data.updates.items() if key in {"name", "country", "sport", "rulebook", "licensing_requirements"}})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Update Rulebook
# ---------------------------------------------------------
@router.put("/{federation_id}/rulebook")
def update_rulebook(federation_id: int, data: RulebookUpdate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    _require_owner(db, federation_id, user_id)
    try:
        return crud.update_rulebook(db, federation_id, data.rulebook)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Update Licensing Requirements
# ---------------------------------------------------------
@router.put("/{federation_id}/licensing")
def update_licensing(federation_id: int, data: LicensingUpdate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    _require_owner(db, federation_id, user_id)
    try:
        return crud.update_licensing(db, federation_id, data.licensing_requirements)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Deactivate Federation
# ---------------------------------------------------------
@router.delete("/{federation_id}/deactivate")
def deactivate_federation(federation_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    _require_owner(db, federation_id, user_id)
    try:
        return crud.deactivate_federation(db, federation_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


def _require_member(db: Session, federation_id: int, user_id: int):
    member = db.query(FederationMembership).filter_by(federation_id=federation_id, user_id=user_id).first()
    user = db.query(User).filter_by(id=user_id).first()
    if not member and not (user and user.is_admin):
        raise HTTPException(status_code=404, detail="Federation not found")


def _require_owner(db: Session, federation_id: int, user_id: int):
    member = db.query(FederationMembership).filter_by(federation_id=federation_id, user_id=user_id, role="owner").first()
    user = db.query(User).filter_by(id=user_id).first()
    if not member and not (user and user.is_admin):
        raise HTTPException(status_code=403, detail="Federation owner role required")


@router.post("/{federation_id}/join")
def join_federation(federation_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    if not db.query(Federation).filter_by(id=federation_id, is_active=True).first():
        raise HTTPException(status_code=404, detail="Federation not found")
    member = db.query(FederationMembership).filter_by(federation_id=federation_id, user_id=user_id).first()
    if member is None:
        db.add(FederationMembership(federation_id=federation_id, user_id=user_id, role="member"))
        db.commit()
    return {"federation_id": federation_id, "joined": True}


@router.delete("/{federation_id}/join")
def leave_federation(federation_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    member = db.query(FederationMembership).filter_by(federation_id=federation_id, user_id=user_id, role="member").first()
    if member:
        db.delete(member)
        db.commit()
    return {"federation_id": federation_id, "joined": False}


@router.get("/{federation_id}/members")
def federation_members(federation_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    _require_member(db, federation_id, user_id)
    rows = db.query(FederationMembership, User.name).join(User, User.id == FederationMembership.user_id).filter(FederationMembership.federation_id == federation_id).all()
    return [{"user_id": row.user_id, "name": name, "role": row.role} for row, name in rows]
