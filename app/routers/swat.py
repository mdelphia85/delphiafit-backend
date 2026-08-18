from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database.connection import get_db
from app.crud.swat import SWATCRUD

router = APIRouter(prefix="/swat", tags=["SWAT Prep"])
crud = SWATCRUD()


# ---------------------------------------------------------
# Schemas
# ---------------------------------------------------------

class PipelineCreate(BaseModel):
    name: str
    agency: str
    description: Optional[str] = None


class DrillCreate(BaseModel):
    pipeline_id: int
    name: str
    drill_type: str
    standard: Optional[float] = None
    description: Optional[str] = None


class OperatorCreate(BaseModel):
    user_id: int
    pipeline_id: int


class EvaluationCreate(BaseModel):
    operator_id: int
    drill_id: int
    score: Optional[float] = None
    passed: Optional[bool] = False
    notes: Optional[str] = None


# ---------------------------------------------------------
# Pipelines
# ---------------------------------------------------------
@router.post("/pipeline")
def create_pipeline(data: PipelineCreate, db: Session = Depends(get_db)):
    return crud.create_pipeline(db, data.model_dump())


@router.get("/pipeline/list")
def list_pipelines(db: Session = Depends(get_db)):
    return crud.list_pipelines(db)


# ---------------------------------------------------------
# Drills
# ---------------------------------------------------------
@router.post("/drill")
def add_drill(data: DrillCreate, db: Session = Depends(get_db)):
    return crud.add_drill(db, data.model_dump())


@router.get("/drill/{pipeline_id}")
def list_drills(pipeline_id: int, db: Session = Depends(get_db)):
    return crud.list_drills(db, pipeline_id)


# ---------------------------------------------------------
# Operators
# ---------------------------------------------------------
@router.post("/operator")
def add_operator(data: OperatorCreate, db: Session = Depends(get_db)):
    return crud.add_operator(db, data.model_dump())


@router.get("/operator/{pipeline_id}")
def list_operators(pipeline_id: int, db: Session = Depends(get_db)):
    return crud.list_operators(db, pipeline_id)


# ---------------------------------------------------------
# Evaluations
# ---------------------------------------------------------
@router.post("/evaluation")
def evaluate(data: EvaluationCreate, db: Session = Depends(get_db)):
    return crud.evaluate(db, data.model_dump())


@router.get("/evaluation/{operator_id}")
def get_evaluations(operator_id: int, db: Session = Depends(get_db)):
    return crud.get_evaluations(db, operator_id)
