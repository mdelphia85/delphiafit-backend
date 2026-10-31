from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.coach_dependencies import get_current_coach
from app.database.connection import get_db
from app.crud.academy import AcademyCRUD
from app.models.academy import AcademyCadet, AcademyModule, AcademyProgram
from app.utils.security import get_current_user_id

router = APIRouter(prefix="/academy", tags=["Academy"])
crud = AcademyCRUD()


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
    user_id: Optional[int] = None
    program_id: int


class EvaluationCreate(BaseModel):
    cadet_id: int
    module_id: int
    score: Optional[float] = None
    passed: Optional[bool] = False
    notes: Optional[str] = None


@router.post("/program")
def create_program(data: ProgramCreate, coach=Depends(get_current_coach), db: Session = Depends(get_db)):
    return crud.create_program(db, data.model_dump())


@router.get("/program/list")
def list_programs(db: Session = Depends(get_db)):
    return crud.list_programs(db)


@router.post("/module")
def add_module(data: ModuleCreate, coach=Depends(get_current_coach), db: Session = Depends(get_db)):
    if db.query(AcademyProgram.id).filter(AcademyProgram.id == data.program_id, AcademyProgram.active.is_(True)).first() is None:
        raise HTTPException(status_code=404, detail="Academy program not found.")
    return crud.add_module(db, data.model_dump())


@router.get("/module/{program_id}")
def list_modules(program_id: int, db: Session = Depends(get_db)):
    return crud.list_modules(db, program_id)


@router.post("/cadet/enroll")
def enroll_cadet(data: CadetEnroll, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    if db.query(AcademyProgram.id).filter(AcademyProgram.id == data.program_id, AcademyProgram.active.is_(True)).first() is None:
        raise HTTPException(status_code=404, detail="Academy program not found.")
    return crud.enroll_cadet(db, {"user_id": user_id, "program_id": data.program_id})


@router.get("/cadet/{program_id}")
def list_cadets(program_id: int, coach=Depends(get_current_coach), db: Session = Depends(get_db)):
    if db.query(AcademyProgram.id).filter(AcademyProgram.id == program_id).first() is None:
        raise HTTPException(status_code=404, detail="Academy program not found.")
    return crud.list_cadets(db, program_id)


@router.post("/evaluation")
def evaluate(data: EvaluationCreate, coach=Depends(get_current_coach), db: Session = Depends(get_db)):
    cadet = db.query(AcademyCadet).filter(AcademyCadet.id == data.cadet_id).first()
    module = db.query(AcademyModule).filter(AcademyModule.id == data.module_id).first()
    if cadet is None or module is None or cadet.program_id != module.program_id:
        raise HTTPException(status_code=404, detail="Cadet or academy module not found.")
    return crud.evaluate(db, data.model_dump())


@router.get("/evaluation/{cadet_id}")
def get_evaluations(cadet_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    cadet = db.query(AcademyCadet).filter(AcademyCadet.id == cadet_id, AcademyCadet.user_id == user_id).first()
    if cadet is None:
        raise HTTPException(status_code=404, detail="Cadet record not found.")
    return crud.get_evaluations(db, cadet_id)
