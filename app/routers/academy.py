from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database.connection import get_db
from app.crud.academy import AcademyCRUD

router = APIRouter(prefix="/academy", tags=["Academy"])
crud = AcademyCRUD()


# ---------------------------------------------------------
# Schemas
# ---------------------------------------------------------

class ProgramCreate(BaseModel):
    name: str
    category: str
    description: Optional[str] = None


class ModuleCreate(BaseModel):
    program_id: int
    name: str
    module_type: str
    description: Optional[str] = None


class CadetEnroll(BaseModel):
    user_id: int
    program_id: int


class EvaluationCreate(BaseModel):
    cadet_id: int
    module_id: int
    score: Optional[float] = None
    passed: Optional[bool] = False
    notes: Optional[str] = None


# ---------------------------------------------------------
# Programs
# ---------------------------------------------------------
@router.post("/program")
def create_program(data: ProgramCreate, db: Session = Depends(get_db)):
    return crud.create_program(db, data.model_dump())


@router.get("/program/list")
def list_programs(db: Session = Depends(get_db)):
    return crud.list_programs(db)


# ---------------------------------------------------------
# Modules
# ---------------------------------------------------------
@router.post("/module")
def add_module(data: ModuleCreate, db: Session = Depends(get_db)):
    return crud.add_module(db, data.model_dump())


@router.get("/module/{program_id}")
def list_modules(program_id: int, db: Session = Depends(get_db)):
    return crud.list_modules(db, program_id)


# ---------------------------------------------------------
# Cadets
# ---------------------------------------------------------
@router.post("/cadet/enroll")
def enroll_cadet(data: CadetEnroll, db: Session = Depends(get_db)):
    return crud.enroll_cadet(db, data.model_dump())


@router.get("/cadet/{program_id}")
def list_cadets(program_id: int, db: Session = Depends(get_db)):
    return crud.list_cadets(db, program_id)


# ---------------------------------------------------------
# Evaluations
# ---------------------------------------------------------
@router.post("/evaluation")
def evaluate(data: EvaluationCreate, db: Session = Depends(get_db)):
    return crud.evaluate(db, data.model_dump())


@router.get("/evaluation/{cadet_id}")
def get_evaluations(cadet_id: int, db: Session = Depends(get_db)):
    return crud.get_evaluations(db, cadet_id)
