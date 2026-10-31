from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.crud.swat import SWATCRUD
from app.models.swat import SWATPipeline, SWATDrill, SWATOperator
from app.utils.security import get_current_user_id

router = APIRouter(prefix="/swat", tags=["SWAT Prep"])
crud = SWATCRUD()


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
    pipeline_id: int

class EvaluationCreate(BaseModel):
    operator_id: int
    drill_id: int
    score: Optional[float] = None
    passed: Optional[bool] = False
    notes: Optional[str] = None


def require_pipeline(db: Session, pipeline_id: int, user_id: int, allow_catalog: bool = True):
    query = db.query(SWATPipeline).filter(SWATPipeline.id == pipeline_id)
    if allow_catalog:
        query = query.filter((SWATPipeline.owner_user_id.is_(None)) | (SWATPipeline.owner_user_id == user_id))
    else:
        query = query.filter(SWATPipeline.owner_user_id == user_id)
    pipeline = query.first()
    if pipeline is None:
        raise HTTPException(status_code=404, detail="Pipeline not found.")
    return pipeline


def require_operator(db: Session, operator_id: int, user_id: int):
    operator = db.query(SWATOperator).filter(SWATOperator.id == operator_id, SWATOperator.user_id == user_id).first()
    if operator is None:
        raise HTTPException(status_code=404, detail="Operator not found.")
    return operator


@router.post("/pipeline")
def create_pipeline(data: PipelineCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return crud.create_pipeline(db, {**data.model_dump(), "owner_user_id": user_id})

@router.get("/pipeline/list")
def list_pipelines(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return crud.list_pipelines(db, user_id)

@router.post("/drill")
def add_drill(data: DrillCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    require_pipeline(db, data.pipeline_id, user_id, allow_catalog=False)
    return crud.add_drill(db, data.model_dump())

@router.get("/drill/{pipeline_id}")
def list_drills(pipeline_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    require_pipeline(db, pipeline_id, user_id)
    return crud.list_drills(db, pipeline_id)

@router.post("/operator")
def add_operator(data: OperatorCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    require_pipeline(db, data.pipeline_id, user_id)
    return crud.add_operator(db, {"pipeline_id": data.pipeline_id, "user_id": user_id})

@router.get("/operator/{pipeline_id}")
def list_operators(pipeline_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    require_pipeline(db, pipeline_id, user_id)
    return crud.list_operators(db, pipeline_id, user_id)

@router.post("/evaluation")
def evaluate(data: EvaluationCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    operator = require_operator(db, data.operator_id, user_id)
    drill = db.query(SWATDrill).filter(SWATDrill.id == data.drill_id, SWATDrill.pipeline_id == operator.pipeline_id).first()
    if drill is None:
        raise HTTPException(status_code=404, detail="Drill not found.")
    return crud.evaluate(db, data.model_dump())

@router.get("/evaluation/{operator_id}")
def get_evaluations(operator_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    require_operator(db, operator_id, user_id)
    return crud.get_evaluations(db, operator_id)
