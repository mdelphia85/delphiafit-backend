from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.utils.security import get_current_user_id
from app.crud.hazmat import HazmatCRUD
from app.models.hazmat import HazmatOperation

router = APIRouter(prefix="/hazmat", tags=["Hazmat"])
crud = HazmatCRUD()


def require_owned(db: Session, object_id: int, user_id: int):
    obj = db.query(HazmatOperation).filter(HazmatOperation.id == object_id, HazmatOperation.owner_user_id == user_id).first()
    if obj is None:
        raise HTTPException(status_code=404, detail="Record not found.")
    return obj

class OperationCreate(BaseModel):
    name: str
    incident_type: str
    location: Optional[str] = None
    threat_level: Optional[str] = None
    notes: Optional[str] = None

class ZoneCreate(BaseModel):
    operation_id: int
    zone_type: str
    description: Optional[str] = None
    status: Optional[str] = "active"

class ResourceCreate(BaseModel):
    operation_id: int
    resource_type: str
    quantity: Optional[int] = 1
    assigned_zone: Optional[str] = None
    notes: Optional[str] = None

class ExposureCreate(BaseModel):
    operation_id: int
    exposure_type: str
    severity: Optional[str] = None
    notes: Optional[str] = None

class OperationClose(BaseModel):
    status: Optional[str] = "completed"


@router.post("/operation")
def create_operation(data: OperationCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return crud.create_operation(db, {**data.model_dump(), "incident_commander_id": user_id, "owner_user_id": user_id})

@router.get("/operation/list")
def list_operations(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return crud.list_operations(db, user_id)

@router.get("/operation/{op_id}")
def get_operation(op_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return require_owned(db, op_id, user_id)

@router.post("/operation/{op_id}/close")
def close_operation(op_id: int, data: OperationClose, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    try:
        return crud.close_operation(db, op_id, user_id, data.status)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

@router.post("/zone")
def add_zone(data: ZoneCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    require_owned(db, data.operation_id, user_id)
    return crud.add_zone(db, data.model_dump())

@router.get("/zone/{operation_id}")
def list_zones(operation_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    require_owned(db, operation_id, user_id)
    return crud.list_zones(db, operation_id)

@router.post("/resource")
def add_resource(data: ResourceCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    require_owned(db, data.operation_id, user_id)
    return crud.add_resource(db, data.model_dump())

@router.get("/resource/{operation_id}")
def list_resources(operation_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    require_owned(db, operation_id, user_id)
    return crud.list_resources(db, operation_id)

@router.post("/exposure")
def log_exposure(data: ExposureCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    require_owned(db, data.operation_id, user_id)
    return crud.log_exposure(db, {**data.model_dump(), "responder_id": user_id})

@router.get("/exposure/{operation_id}")
def list_exposures(operation_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    require_owned(db, operation_id, user_id)
    return crud.list_exposures(db, operation_id)
