from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database.connection import get_db
from app.crud.hazmat import HazmatCRUD

router = APIRouter(prefix="/hazmat", tags=["Hazmat"])
crud = HazmatCRUD()


class OperationCreate(BaseModel):
    name: str
    incident_type: str
    incident_commander_id: int
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
    responder_id: int
    exposure_type: str
    severity: Optional[str] = None
    notes: Optional[str] = None


class OperationClose(BaseModel):
    status: Optional[str] = "completed"


@router.post("/operation")
def create_operation(data: OperationCreate, db: Session = Depends(get_db)):
    return crud.create_operation(db, data.dict())


@router.get("/operation/list")
def list_operations(db: Session = Depends(get_db)):
    return crud.list_operations(db)


@router.get("/operation/{op_id}")
def get_operation(op_id: int, db: Session = Depends(get_db)):
    op = crud.get_operation(db, op_id)
    if not op:
        raise HTTPException(status_code=404, detail="Operation not found.")
    return op


@router.post("/operation/{op_id}/close")
def close_operation(op_id: int, data: OperationClose, db: Session = Depends(get_db)):
    try:
        return crud.close_operation(db, op_id, data.status)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/zone")
def add_zone(data: ZoneCreate, db: Session = Depends(get_db)):
    return crud.add_zone(db, data.dict())


@router.get("/zone/{operation_id}")
def list_zones(operation_id: int, db: Session = Depends(get_db)):
    return crud.list_zones(db, operation_id)


@router.post("/resource")
def add_resource(data: ResourceCreate, db: Session = Depends(get_db)):
    return crud.add_resource(db, data.dict())


@router.get("/resource/{operation_id}")
def list_resources(operation_id: int, db: Session = Depends(get_db)):
    return crud.list_resources(db, operation_id)


@router.post("/exposure")
def log_exposure(data: ExposureCreate, db: Session = Depends(get_db)):
    return crud.log_exposure(db, data.dict())


@router.get("/exposure/{operation_id}")
def list_exposures(operation_id: int, db: Session = Depends(get_db)):
    return crud.list_exposures(db, operation_id)
