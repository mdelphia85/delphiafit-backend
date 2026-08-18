from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.database.connection import get_db
from app.crud.federation import FederationCRUD

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
def create_federation(data: FederationCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_federation(db, data.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Get Federation by ID
# ---------------------------------------------------------
@router.get("/{federation_id:int}")
def get_federation(federation_id: int, db: Session = Depends(get_db)):
    fed = crud.get_federation(db, federation_id)
    if not fed:
        raise HTTPException(status_code=404, detail="Federation not found.")
    return fed


# ---------------------------------------------------------
# List Federations
# ---------------------------------------------------------
@router.get("/list")
def list_federations(db: Session = Depends(get_db)):
    return crud.list_federations(db)


# ---------------------------------------------------------
# Update Federation
# ---------------------------------------------------------
@router.put("/{federation_id}/update")
def update_federation(federation_id: int, data: FederationUpdate, db: Session = Depends(get_db)):
    try:
        return crud.update_federation(db, federation_id, data.updates)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Update Rulebook
# ---------------------------------------------------------
@router.put("/{federation_id}/rulebook")
def update_rulebook(federation_id: int, data: RulebookUpdate, db: Session = Depends(get_db)):
    try:
        return crud.update_rulebook(db, federation_id, data.rulebook)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Update Licensing Requirements
# ---------------------------------------------------------
@router.put("/{federation_id}/licensing")
def update_licensing(federation_id: int, data: LicensingUpdate, db: Session = Depends(get_db)):
    try:
        return crud.update_licensing(db, federation_id, data.licensing_requirements)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Deactivate Federation
# ---------------------------------------------------------
@router.delete("/{federation_id}/deactivate")
def deactivate_federation(federation_id: int, db: Session = Depends(get_db)):
    try:
        return crud.deactivate_federation(db, federation_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
