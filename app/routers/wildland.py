from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.utils.security import get_current_user_id
from app.crud.wildland import WildlandCRUD
from app.models.wildland import WildlandOperation

router = APIRouter(prefix="/wildland", tags=["Wildland Fire"])
crud = WildlandCRUD()


def require_owned(db: Session, object_id: int, user_id: int):
    obj = db.query(WildlandOperation).filter(WildlandOperation.id == object_id, WildlandOperation.owner_user_id == user_id).first()
    if obj is None:
        raise HTTPException(status_code=404, detail="Record not found.")
    return obj

class OperationCreate(BaseModel):
    name: str
    fire_type: str
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
def create_operation(data: OperationCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return crud.create_operation(db, {**data.model_dump(), "incident_commander_id": user_id, "owner_user_id": user_id})

@router.get("/operation/list")
def list_operations(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return crud.list_operations(db, user_id)

@router.get("/operation/{op_id}")
def get_operation(op_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return require_owned(db, op_id, user_id)

@router.post("/operation/{op_id}/containment")
def update_containment(op_id: int, data: ContainmentUpdate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    try:
        return crud.update_containment(db, op_id, user_id, data.containment)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

@router.post("/operation/{op_id}/close")
def close_operation(op_id: int, data: OperationClose, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    try:
        return crud.close_operation(db, op_id, user_id, data.status)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

@router.post("/division")
def add_division(data: DivisionCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    require_owned(db, data.operation_id, user_id)
    return crud.add_division(db, data.model_dump())

@router.get("/division/{operation_id}")
def list_divisions(operation_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    require_owned(db, operation_id, user_id)
    return crud.list_divisions(db, operation_id)

@router.post("/resource")
def add_resource(data: ResourceCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    require_owned(db, data.operation_id, user_id)
    return crud.add_resource(db, data.model_dump())

@router.get("/resource/{operation_id}")
def list_resources(operation_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    require_owned(db, operation_id, user_id)
    return crud.list_resources(db, operation_id)

@router.post("/event")
def log_event(data: EventCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    require_owned(db, data.operation_id, user_id)
    return crud.log_event(db, data.model_dump())

@router.get("/event/{operation_id}")
def list_events(operation_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    require_owned(db, operation_id, user_id)
    return crud.list_events(db, operation_id)
