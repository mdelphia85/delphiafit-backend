from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.utils.security import get_current_user_id
from app.crud.search_rescue import SearchRescueCRUD
from app.models.search_rescue import SearchRescue

router = APIRouter(prefix="/sar", tags=["Search & Rescue"])
crud = SearchRescueCRUD()


def require_owned(db: Session, object_id: int, user_id: int):
    obj = db.query(SearchRescue).filter(SearchRescue.id == object_id, SearchRescue.owner_user_id == user_id).first()
    if obj is None:
        raise HTTPException(status_code=404, detail="Record not found.")
    return obj

class OperationCreate(BaseModel):
    operation_name: str
    operation_type: str
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


@router.post("/operation")
def create_operation(data: OperationCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return crud.create_operation(db, {**data.model_dump(), "commander_id": user_id, "owner_user_id": user_id})

@router.get("/operation/list")
def list_operations(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return crud.list_operations(db, user_id)

@router.post("/team")
def add_team(data: TeamCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    require_owned(db, data.operation_id, user_id)
    return crud.add_team(db, data.model_dump())

@router.get("/team/{op_id}")
def list_teams(op_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    require_owned(db, op_id, user_id)
    return crud.list_teams(db, op_id)

@router.post("/victim")
def add_victim(data: VictimCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    require_owned(db, data.operation_id, user_id)
    return crud.add_victim(db, data.model_dump())

@router.get("/operation/{op_id}")
def get_operation(op_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return require_owned(db, op_id, user_id)
