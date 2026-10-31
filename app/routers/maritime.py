from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.utils.security import get_current_user_id
from app.crud.maritime import MaritimeCRUD
from app.models.maritime import MaritimeOperation

router = APIRouter(prefix="/maritime", tags=["Maritime"])
crud = MaritimeCRUD()


def require_owned(db: Session, object_id: int, user_id: int):
    obj = db.query(MaritimeOperation).filter(MaritimeOperation.id == object_id, MaritimeOperation.owner_user_id == user_id).first()
    if obj is None:
        raise HTTPException(status_code=404, detail="Record not found.")
    return obj

class OperationCreate(BaseModel):
    name: str
    operation_type: str
    vessel: Optional[str] = None
    location: Optional[str] = None
    sea_state: Optional[str] = None
    notes: Optional[str] = None

class CrewCreate(BaseModel):
    operation_id: int
    role: str
    member_name: str
    certification: Optional[str] = None

class IncidentCreate(BaseModel):
    operation_id: int
    incident_type: str
    description: Optional[str] = None
    severity: Optional[str] = None

class OperationClose(BaseModel):
    status: Optional[str] = "completed"


@router.post("/operation")
def create_operation(data: OperationCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return crud.create_operation(db, {**data.model_dump(), "commander_id": user_id, "owner_user_id": user_id})

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

@router.post("/incident")
def log_incident(data: IncidentCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    require_owned(db, data.operation_id, user_id)
    return crud.log_incident(db, data.model_dump())

@router.get("/incident/{operation_id}")
def list_incidents(operation_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    require_owned(db, operation_id, user_id)
    return crud.list_incidents(db, operation_id)
