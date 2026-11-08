from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.crud.org import OrgCRUD
from app.models.org import Organization
from app.models.org_membership import OrganizationMembership
from app.models.user import User
from app.utils.security import get_current_user_id

router = APIRouter(prefix="/org", tags=["Organization"])
crud = OrgCRUD()


class OrgCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
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


class RoleUpdate(BaseModel):
    role: str


class MemberAdd(BaseModel):
    email: str
    role: str = "member"


ALLOWED_ORG_FIELDS = {"name", "industry", "country", "timezone", "contact_email", "contact_phone"}
ALLOWED_SETTING_FIELDS = {"compliance_rules", "forecasting_model", "ai_mode", "dashboard_config"}
VALID_ROLES = {"admin", "manager", "member"}


def _serialize(row):
    return {column.name: getattr(row, column.name) for column in row.__table__.columns}


def _membership(db: Session, org_id: int, user_id: int):
    return db.query(OrganizationMembership).filter_by(organization_id=org_id, user_id=user_id).first()


def _require_member(db: Session, org_id: int, user_id: int, admin: bool = False):
    membership = _membership(db, org_id, user_id)
    if membership is None:
        raise HTTPException(status_code=404, detail="Organization not found.")
    if admin and membership.role not in {"owner", "admin"}:
        raise HTTPException(status_code=403, detail="Organization admin role required.")
    return membership


@router.post("/create")
def create_org(data: OrgCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    try:
        org = crud.create_org(db, data.model_dump())
        db.add(OrganizationMembership(organization_id=org.id, user_id=user_id, role="owner"))
        db.commit()
        return _serialize(org)
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/mine")
@router.get("/list")
def list_orgs(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    rows = (db.query(Organization).join(OrganizationMembership, OrganizationMembership.organization_id == Organization.id)
            .filter(OrganizationMembership.user_id == user_id, Organization.is_active.is_(True)).all())
    return [_serialize(row) for row in rows]


@router.get("/{org_id:int}")
def get_org(org_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    _require_member(db, org_id, user_id)
    org = crud.get_org(db, org_id)
    if not org or not org.is_active:
        raise HTTPException(status_code=404, detail="Organization not found.")
    return _serialize(org)


@router.put("/{org_id}/update")
def update_org(org_id: int, data: OrgUpdate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    _require_member(db, org_id, user_id, admin=True)
    updates = {key: value for key, value in data.updates.items() if key in ALLOWED_ORG_FIELDS}
    try:
        return _serialize(crud.update_org(db, org_id, updates))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{org_id}/deactivate")
def deactivate_org(org_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    _require_member(db, org_id, user_id, admin=True)
    try:
        return _serialize(crud.deactivate_org(db, org_id))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{org_id}/tenant/create")
def create_tenant(org_id: int, data: TenantCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    _require_member(db, org_id, user_id, admin=True)
    try:
        return _serialize(crud.create_tenant(db, org_id, data.name, data.description))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{org_id}/tenant/list")
def list_tenants(org_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    _require_member(db, org_id, user_id)
    return [_serialize(row) for row in crud.list_tenants(db, org_id)]


@router.get("/{org_id}/settings")
def get_settings(org_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    _require_member(db, org_id, user_id)
    row = db.query(Organization).filter(Organization.id == org_id).first()
    if not row or not row.enterprise_settings:
        raise HTTPException(status_code=404, detail="Organization settings not found.")
    return _serialize(row.enterprise_settings)


@router.put("/{org_id}/settings/update")
def update_settings(org_id: int, data: SettingsUpdate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    _require_member(db, org_id, user_id, admin=True)
    updates = {key: value for key, value in data.updates.items() if key in ALLOWED_SETTING_FIELDS}
    try:
        return _serialize(crud.update_settings(db, org_id, updates))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{org_id}/members")
def add_member(org_id: int, data: MemberAdd, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    _require_member(db, org_id, user_id, admin=True)
    if data.role not in {"admin", "manager", "member"}:
        raise HTTPException(status_code=422, detail="New members may be assigned admin, manager, or member roles.")
    user = db.query(User).filter(func.lower(User.email) == data.email.strip().lower()).first()
    if user is None:
        raise HTTPException(status_code=404, detail="No account was found for that email.")
    if _membership(db, org_id, user.id):
        raise HTTPException(status_code=409, detail="That user is already a member.")
    membership = OrganizationMembership(organization_id=org_id, user_id=user.id, role=data.role)
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return {"id": membership.id, "user_id": membership.user_id, "role": membership.role, "created_at": membership.created_at}


@router.get("/{org_id}/members")
def list_members(org_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    _require_member(db, org_id, user_id, admin=True)
    rows = db.query(OrganizationMembership).filter_by(organization_id=org_id).all()
    return [{"id": row.id, "user_id": row.user_id, "role": row.role, "created_at": row.created_at} for row in rows]


@router.patch("/{org_id}/members/{membership_id}/role")
def update_member_role(org_id: int, membership_id: int, data: RoleUpdate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    _require_member(db, org_id, user_id, admin=True)
    if data.role not in VALID_ROLES:
        raise HTTPException(status_code=422, detail="Role must be admin, manager, or member.")
    member = db.query(OrganizationMembership).filter_by(id=membership_id, organization_id=org_id).first()
    if member is None:
        raise HTTPException(status_code=404, detail="Organization member not found.")
    if member.role == "owner" and data.role != "owner":
        raise HTTPException(status_code=400, detail="The organization owner role cannot be removed.")
    member.role = data.role
    db.commit()
    db.refresh(member)
    return {"id": member.id, "user_id": member.user_id, "role": member.role}
