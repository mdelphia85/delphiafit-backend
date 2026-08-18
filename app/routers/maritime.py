from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database.connection import get_db
from app.crud.maritime import MaritimeCRUD

router = APIRouter(prefix="/maritime", tags=["Maritime"])
crud = MaritimeCRUD()


# ---------------------------------------------------------
# Schemas
# ---------------------------------------------------------

class OperationCreate(BaseModel):
    name: str
    operation_type: str
    commander_id: int
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


# ---------------------------------------------------------
# Create Operation
# ---------------------------------------------------------
@router.post("/operation")
def create_operation(data: OperationCreate, db: Session = Depends(get_db)):
    return crud.create_operation(db, data.model_dump())


# ---------------------------------------------------------
# List Operations
# ---------------------------------------------------------
@router.get("/operation/list")
def list_operations(db: Session = Depends(get_db)):
    return crud.list_operations(db)


# ---------------------------------------------------------
# Get Operation
# ---------------------------------------------------------
@router.get("/operation/{op_id}")
def get_operation(op_id: int, db: Session = Depends(get_db)):
    op = crud.get_operation(db, op_id)
    if not op:
        raise HTTPException(status_code=404, detail="Operation not found.")
    return op


# ---------------------------------------------------------
# Close Operation
# ---------------------------------------------------------
@router.post("/operation/{op_id}/close")
def close_operation(op_id: int, data: OperationClose, db: Session = Depends(get_db)):
    try:
        return crud.close_operation(db, op_id, data.status)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ---------------------------------------------------------
# Add Crew Member
# ---------------------------------------------------------
@router.post("/crew")
def add_crew(data: CrewCreate, db: Session = Depends(get_db)):
    return crud.add_crew(db, data.model_dump())


# ---------------------------------------------------------
# List Crew
# ---------------------------------------------------------
@router.get("/crew/{operation_id}")
def list_crew(operation_id: int, db: Session = Depends(get_db)):
    return crud.list_crew(db, operation_id)


# ---------------------------------------------------------
# Log Incident
# ---------------------------------------------------------
@router.post("/incident")
def log_incident(data: IncidentCreate, db: Session = Depends(get_db)):
    return crud.log_incident(db, data.model_dump())


# ---------------------------------------------------------
# List Incidents
# ---------------------------------------------------------
@router.get("/incident/{operation_id}")
def list_incidents(operation_id: int, db: Session = Depends(get_db)):
    return crud.list_incidents(db, operation_id)
