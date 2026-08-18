from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database.connection import get_db
from app.crud.disaster import DisasterCRUD

router = APIRouter(prefix="/disaster", tags=["Disaster Response"])
crud = DisasterCRUD()


# Schemas

class OperationCreate(BaseModel):
    name: str
    type: str
    incident_commander_id: int
    location: Optional[str] = None
    severity: Optional[str] = None
    notes: Optional[str] = None


class SectorCreate(BaseModel):
    operation_id: int
    name: str
    description: Optional[str] = None
    status: Optional[str] = "active"


class ResourceCreate(BaseModel):
    operation_id: int
    resource_type: str
    quantity: Optional[int] = 1
    assigned_sector: Optional[str] = None
    notes: Optional[str] = None


class OperationClose(BaseModel):
    status: Optional[str] = "completed"


# Routes

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


@router.post("/sector")
def add_sector(data: SectorCreate, db: Session = Depends(get_db)):
    return crud.add_sector(db, data.model_dump())


@router.get("/sector/{operation_id}")
def list_sectors(operation_id: int, db: Session = Depends(get_db)):
    return crud.list_sectors(db, operation_id)


@router.post("/resource")
def add_resource(data: ResourceCreate, db: Session = Depends(get_db)):
    return crud.add_resource(db, data.model_dump())


@router.get("/resource/{operation_id}")
def list_resources(operation_id: int, db: Session = Depends(get_db)):
    return crud.list_resources(db, operation_id)
