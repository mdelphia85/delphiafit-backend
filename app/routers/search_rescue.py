from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database.connection import get_db
from app.crud.search_rescue import SearchRescueCRUD

router = APIRouter(prefix="/sar", tags=["Search & Rescue"])
crud = SearchRescueCRUD()


# ---------------------------------------------------------
# Schemas
# ---------------------------------------------------------

class OperationCreate(BaseModel):
    operation_name: str
    operation_type: str
    commander_id: int
    location: Optional[str] = None
    notes: Optional[str] = None


class TeamCreate(BaseModel):
    operation_id: int
    team_name: str
    members: Optional[str] = None
    specialty: Optional[str] = None


class VictimCreate(BaseModel):
    operation_id: int
    name: Optional[str] = None
    condition: Optional[str] = None
    found_at: Optional[str] = None
    extraction_time: Optional[str] = None
    notes: Optional[str] = None


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
# Add Team
# ---------------------------------------------------------
@router.post("/team")
def add_team(data: TeamCreate, db: Session = Depends(get_db)):
    return crud.add_team(db, data.model_dump())


# ---------------------------------------------------------
# Add Victim
# ---------------------------------------------------------
@router.post("/victim")
def add_victim(data: VictimCreate, db: Session = Depends(get_db)):
    return crud.add_victim(db, data.model_dump())


# ---------------------------------------------------------
# Operation Details
# ---------------------------------------------------------
@router.get("/operation/{op_id}")
def get_operation(op_id: int, db: Session = Depends(get_db)):
    op = crud.get_operation(db, op_id)
    if not op:
        raise HTTPException(status_code=404, detail="Operation not found.")
    return op
