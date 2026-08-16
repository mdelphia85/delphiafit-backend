from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.database import get_db
from app.crud.org import OrgCRUD

router = APIRouter(prefix="/org", tags=["Organization"])
crud = OrgCRUD()


# ---------------------------------------------------------
# Request Models
# ---------------------------------------------------------

class OrgCreate(BaseModel):
    name: str
    industry: Optional[str] = None
    country: Optional[str] = None
    timezone: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None


class OrgUpdate(BaseModel):
    updates: Dict[str, Any]


class TenantCreate(BaseModel):
    name: str
    description: Optional[str] = None


class SettingsUpdate(BaseModel):
    updates: Dict[str, Any]


# ---------------------------------------------------------
# Create Organization
# ---------------------------------------------------------
@router.post("/create")
def create_org(data: OrgCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_org(db, data.dict())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Get Organization
# ---------------------------------------------------------
@router.get("/{org_id}")
def get_org(org_id: int, db: Session = Depends(get_db)):
    org = crud.get_org(db, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found.")
    return org


# ---------------------------------------------------------
# List Organizations
# ---------------------------------------------------------
@router.get("/list")
def list_orgs(db: Session = Depends(get_db)):
    return crud.list_orgs(db)


# ---------------------------------------------------------
# Update Organization
# ---------------------------------------------------------
@router.put("/{org_id}/update")
def update_org(org_id: int, data: OrgUpdate, db: Session = Depends(get_db)):
    try:
        return crud.update_org(db, org_id, data.updates)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Deactivate Organization
# ---------------------------------------------------------
@router.delete("/{org_id}/deactivate")
def deactivate_org(org_id: int, db: Session = Depends(get_db)):
    try:
        return crud.deactivate_org(db, org_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Create Tenant
# ---------------------------------------------------------
@router.post("/{org_id}/tenant/create")
def create_tenant(org_id: int, data: TenantCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_tenant(db, org_id, data.name, data.description)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# List Tenants
# ---------------------------------------------------------
@router.get("/{org_id}/tenant/list")
def list_tenants(org_id: int, db: Session = Depends(get_db)):
    return crud.list_tenants(db, org_id)


# ---------------------------------------------------------
# Update Enterprise Settings
# ---------------------------------------------------------
@router.put("/{org_id}/settings/update")
def update_settings(org_id: int, data: SettingsUpdate, db: Session = Depends(get_db)):
    try:
        return crud.update_settings(db, org_id, data.updates)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
