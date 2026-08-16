from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database.connection import get_db
from app.crud.wildland import WildlandCRUD

router = APIRouter(prefix="/wildland", tags=["Wildland Fire"])
crud = WildlandCRUD()


class OperationCreate(BaseModel):
    name: str
    fire_type: str
    incident_commander_id: int
    location: Optional[str] = None
    containment: Optional[float] = 0.0
    notes: Optional[str] = None


class DivisionCreate(BaseModel):
    operation_id: int
    name: str
    status: Optional[str] = "active"
    notes: Optional[str] = None


class ResourceCreate(BaseModel):
    operation_id: int
    resource_type: str
    quantity: Optional[int] = 1
    assigned_division: Optional[str] = None
    notes: Optional[str] = None


class EventCreate(BaseModel):
    operation_id: int
    event_type: str
    description: Optional[str] = None
    severity: Optional[str] = None


class ContainmentUpdate(BaseModel):
    containment: float


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


@router.post("/operation/{op_id}/containment")
def update_containment(op_id: int, data: ContainmentUpdate, db: Session = Depends(get_db)):
    try:
        return crud.update_containment(db, op_id, data.containment)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/operation/{op_id}/close")
def close_operation(op_id: int, data: OperationClose, db: Session = Depends(get_db)):
    try:
        return crud.close_operation(db, op_id, data.status)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/division")
def add_division(data: DivisionCreate, db: Session = Depends(get_db)):
    return crud.add_division(db, data.dict())


@router.get("/division/{operation_id}")
def list_divisions(operation_id: int, db: Session = Depends(get_db)):
    return crud.list_divisions(db, operation_id)


@router.post("/resource")
def add_resource(data: ResourceCreate, db: Session = Depends(get_db)):
    return crud.add_resource(db, data.dict())


@router.get("/resource/{operation_id}")
def list_resources(operation_id: int, db: Session = Depends(get_db)):
    return crud.list_resources(db, operation_id)


@router.post("/event")
def log_event(data: EventCreate, db: Session = Depends(get_db)):
    return crud.log_event(db, data.dict())


@router.get("/event/{operation_id}")
def list_events(operation_id: int, db: Session = Depends(get_db)):
    return crud.list_events(db, operation_id)
