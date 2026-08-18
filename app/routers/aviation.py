from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database.connection import get_db
from app.crud.aviation import AviationCRUD

router = APIRouter(prefix="/aviation", tags=["Aviation"])
crud = AviationCRUD()


class OperationCreate(BaseModel):
    name: str
    operation_type: str
    mission_commander_id: int
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
def create_operation(data: OperationCreate, db: Session = Depends(get_db)):
    return crud.create_operation(db, data.model_dump())


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


@router.post("/crew")
def add_crew(data: CrewCreate, db: Session = Depends(get_db)):
    return crud.add_crew(db, data.model_dump())


@router.get("/crew/{operation_id}")
def list_crew(operation_id: int, db: Session = Depends(get_db)):
    return crud.list_crew(db, operation_id)


@router.post("/event")
def log_event(data: EventCreate, db: Session = Depends(get_db)):
    return crud.log_event(db, data.model_dump())


@router.get("/event/{operation_id}")
def list_events(operation_id: int, db: Session = Depends(get_db)):
    return crud.list_events(db, operation_id)
