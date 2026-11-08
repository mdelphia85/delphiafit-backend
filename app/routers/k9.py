from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.crud.k9 import K9CRUD
from app.utils.security import get_current_user_id

router = APIRouter(prefix="/k9", tags=["K9"])
crud = K9CRUD()


class K9Create(BaseModel):
    name: str
    breed: Optional[str] = None
    age: Optional[int] = None
    agency: Optional[str] = None
    specialty: Optional[str] = None


class DeploymentCreate(BaseModel):
    k9_id: int
    mission_type: str
    location: Optional[str] = None
    notes: Optional[str] = None
    success: Optional[bool] = False


@router.post("/create")
def create_k9(data: K9Create, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return crud.create_k9(db, data.model_dump(), user_id)


@router.get("/list")
def list_k9(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return crud.list_k9(db, user_id)


@router.post("/deploy")
def log_deployment(data: DeploymentCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return crud.log_deployment(db, data.model_dump(), user_id)


@router.get("/history/{k9_id}")
def history(k9_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return crud.get_history(db, k9_id, user_id)
