from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database.connection import get_db
from app.crud.mission_replay import MissionReplayCRUD

router = APIRouter(prefix="/mission_replay", tags=["Mission Replay"])
crud = MissionReplayCRUD()


# ---------------------------------------------------------
# Schemas
# ---------------------------------------------------------

class ReplayStart(BaseModel):
    user_id: int
    mission_type: str
    mission_id: int


class ReplayComplete(BaseModel):
    score: float


class StepCreate(BaseModel):
    replay_id: int
    action_type: str
    description: Optional[str] = None
    score_delta: Optional[float] = 0.0


class AnnotationCreate(BaseModel):
    replay_id: int
    instructor_id: int
    category: str
    note: str


# ---------------------------------------------------------
# Replay
# ---------------------------------------------------------
@router.post("/start")
def start_replay(data: ReplayStart, db: Session = Depends(get_db)):
    return crud.start_replay(db, data.dict())


@router.post("/{replay_id}/complete")
def complete_replay(replay_id: int, data: ReplayComplete, db: Session = Depends(get_db)):
    return crud.complete_replay(db, replay_id, data.score)


@router.get("/{replay_id}")
def get_replay(replay_id: int, db: Session = Depends(get_db)):
    replay = crud.get_replay(db, replay_id)
    if not replay:
        raise HTTPException(status_code=404, detail="Replay not found.")
    return replay


# ---------------------------------------------------------
# Steps
# ---------------------------------------------------------
@router.post("/step")
def add_step(data: StepCreate, db: Session = Depends(get_db)):
    return crud.add_step(db, data.dict())


@router.get("/step/{replay_id}")
def list_steps(replay_id: int, db: Session = Depends(get_db)):
    return crud.list_steps(db, replay_id)


# ---------------------------------------------------------
# Annotations
# ---------------------------------------------------------
@router.post("/annotation")
def add_annotation(data: AnnotationCreate, db: Session = Depends(get_db)):
    return crud.add_annotation(db, data.dict())


@router.get("/annotation/{replay_id}")
def list_annotations(replay_id: int, db: Session = Depends(get_db)):
    return crud.list_annotations(db, replay_id)
