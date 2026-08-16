from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database.connection import get_db
from app.crud.k9 import K9CRUD

router = APIRouter(prefix="/k9", tags=["K9"])
crud = K9CRUD()


# ---------------------------------------------------------
# Schemas
# ---------------------------------------------------------

class K9Create(BaseModel):
    name: str
    breed: Optional[str] = None
    age: Optional[int] = None
    agency: Optional[str] = None
    specialty: Optional[str] = None


class DeploymentCreate(BaseModel):
    k9_id: int
    handler_id: int
    mission_type: str
    location: Optional[str] = None
    notes: Optional[str] = None
    success: Optional[bool] = False


# ---------------------------------------------------------
# Create K9 Unit
# ---------------------------------------------------------
@router.post("/create")
def create_k9(data: K9Create, db: Session = Depends(get_db)):
    return crud.create_k9(db, data.dict())


# ---------------------------------------------------------
# List K9 Units
# ---------------------------------------------------------
@router.get("/list")
def list_k9(db: Session = Depends(get_db)):
    return crud.list_k9(db)


# ---------------------------------------------------------
# Log Deployment
# ---------------------------------------------------------
@router.post("/deploy")
def log_deployment(data: DeploymentCreate, db: Session = Depends(get_db)):
    return crud.log_deployment(db, data.dict())


# ---------------------------------------------------------
# Deployment History
# ---------------------------------------------------------
@router.get("/history/{k9_id}")
def history(k9_id: int, db: Session = Depends(get_db)):
    return crud.get_history(db, k9_id)
