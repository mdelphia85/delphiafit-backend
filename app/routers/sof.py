from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database.connection import get_db
from app.crud.sof import SOFCRUD

router = APIRouter(prefix="/sof", tags=["SOF Prep"])
crud = SOFCRUD()


# ---------------------------------------------------------
# Schemas
# ---------------------------------------------------------

class PipelineCreate(BaseModel):
    name: str
    branch: str
    description: Optional[str] = None


class EventCreate(BaseModel):
    pipeline_id: int
    name: str
    event_type: str
    standard: Optional[float] = None
    description: Optional[str] = None


class CandidateCreate(BaseModel):
    user_id: int
    pipeline_id: int


class EvaluationCreate(BaseModel):
    candidate_id: int
    event_id: int
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
# Events
# ---------------------------------------------------------
@router.post("/event")
def add_event(data: EventCreate, db: Session = Depends(get_db)):
    return crud.add_event(db, data.model_dump())


@router.get("/event/{pipeline_id}")
def list_events(pipeline_id: int, db: Session = Depends(get_db)):
    return crud.list_events(db, pipeline_id)


# ---------------------------------------------------------
# Candidates
# ---------------------------------------------------------
@router.post("/candidate")
def add_candidate(data: CandidateCreate, db: Session = Depends(get_db)):
    return crud.add_candidate(db, data.model_dump())


@router.get("/candidate/{pipeline_id}")
def list_candidates(pipeline_id: int, db: Session = Depends(get_db)):
    return crud.list_candidates(db, pipeline_id)


# ---------------------------------------------------------
# Evaluations
# ---------------------------------------------------------
@router.post("/evaluation")
def evaluate(data: EvaluationCreate, db: Session = Depends(get_db)):
    return crud.evaluate(db, data.model_dump())


@router.get("/evaluation/{candidate_id}")
def get_evaluations(candidate_id: int, db: Session = Depends(get_db)):
    return crud.get_evaluations(db, candidate_id)
