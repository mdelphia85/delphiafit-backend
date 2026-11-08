from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.utils.security import get_current_user_id
from app.crud.aviation import AviationCRUD
from app.models.aviation import AviationOperation

router = APIRouter(prefix="/aviation", tags=["Aviation"])
crud = AviationCRUD()


def require_owned(db: Session, object_id: int, user_id: int):
    obj = db.query(AviationOperation).filter(AviationOperation.id == object_id, AviationOperation.owner_user_id == user_id).first()
    if obj is None:
        raise HTTPException(status_code=404, detail="Record not found.")
    return obj

class OperationCreate(BaseModel):
    name: str
    operation_type: str
    aircraft: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None

class CrewCreate(BaseModel):
    operation_id: int
    role: str
    member_name: str
    certification: Optional[str] = None

class EventCreate(BaseModel):
    operation_id: int
    event_type: str
    description: Optional[str] = None
    severity: Optional[str] = None

class OperationClose(BaseModel):
    status: Optional[str] = "completed"


@router.post("/operation")
def create_operation(data: OperationCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return crud.create_operation(db, {**data.model_dump(), "mission_commander_id": user_id, "owner_user_id": user_id})

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

@router.post("/crew")
def add_crew(data: CrewCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    require_owned(db, data.operation_id, user_id)
    return crud.add_crew(db, data.model_dump())

@router.get("/crew/{operation_id}")
def list_crew(operation_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    require_owned(db, operation_id, user_id)
    return crud.list_crew(db, operation_id)

@router.post("/event")
def log_event(data: EventCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    require_owned(db, data.operation_id, user_id)
    return crud.log_event(db, data.model_dump())

@router.get("/event/{operation_id}")
def list_events(operation_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    require_owned(db, operation_id, user_id)
    return crud.list_events(db, operation_id)
