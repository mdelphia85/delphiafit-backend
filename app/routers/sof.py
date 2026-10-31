from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.crud.sof import SOFCRUD
from app.models.sof import SOFPipeline, SOFEvent, SOFCandidate
from app.utils.security import get_current_user_id

router = APIRouter(prefix="/sof", tags=["SOF Prep"])
crud = SOFCRUD()


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
    pipeline_id: int

class EvaluationCreate(BaseModel):
    candidate_id: int
    event_id: int
    score: Optional[float] = None
    passed: Optional[bool] = False
    notes: Optional[str] = None


def require_pipeline(db: Session, pipeline_id: int, user_id: int, allow_catalog: bool = True):
    query = db.query(SOFPipeline).filter(SOFPipeline.id == pipeline_id)
    if allow_catalog:
        query = query.filter((SOFPipeline.owner_user_id.is_(None)) | (SOFPipeline.owner_user_id == user_id))
    else:
        query = query.filter(SOFPipeline.owner_user_id == user_id)
    pipeline = query.first()
    if pipeline is None:
        raise HTTPException(status_code=404, detail="Pipeline not found.")
    return pipeline


def require_candidate(db: Session, candidate_id: int, user_id: int):
    candidate = db.query(SOFCandidate).filter(SOFCandidate.id == candidate_id, SOFCandidate.user_id == user_id).first()
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found.")
    return candidate


@router.post("/pipeline")
def create_pipeline(data: PipelineCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return crud.create_pipeline(db, {**data.model_dump(), "owner_user_id": user_id})

@router.get("/pipeline/list")
def list_pipelines(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return crud.list_pipelines(db, user_id)

@router.post("/event")
def add_event(data: EventCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    require_pipeline(db, data.pipeline_id, user_id, allow_catalog=False)
    return crud.add_event(db, data.model_dump())

@router.get("/event/{pipeline_id}")
def list_events(pipeline_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    require_pipeline(db, pipeline_id, user_id)
    return crud.list_events(db, pipeline_id)

@router.post("/candidate")
def add_candidate(data: CandidateCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    require_pipeline(db, data.pipeline_id, user_id)
    return crud.add_candidate(db, {"pipeline_id": data.pipeline_id, "user_id": user_id})

@router.get("/candidate/{pipeline_id}")
def list_candidates(pipeline_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    require_pipeline(db, pipeline_id, user_id)
    return crud.list_candidates(db, pipeline_id, user_id)

@router.post("/evaluation")
def evaluate(data: EvaluationCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    candidate = require_candidate(db, data.candidate_id, user_id)
    event = db.query(SOFEvent).filter(SOFEvent.id == data.event_id, SOFEvent.pipeline_id == candidate.pipeline_id).first()
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found.")
    return crud.evaluate(db, data.model_dump())

@router.get("/evaluation/{candidate_id}")
def get_evaluations(candidate_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    require_candidate(db, candidate_id, user_id)
    return crud.get_evaluations(db, candidate_id)
