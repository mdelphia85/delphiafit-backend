from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.crud.mission_replay import MissionReplayCRUD
from app.utils.security import get_current_user_id

router = APIRouter(prefix="/mission_replay", tags=["Mission Replay"])
crud = MissionReplayCRUD()


class ReplayStart(BaseModel):
    mission_type: str = Field(min_length=1, max_length=80)
    mission_id: int


class ReplayComplete(BaseModel):
    score: float = Field(ge=0, le=100)


class StepCreate(BaseModel):
    replay_id: int
    action_type: str = Field(min_length=1, max_length=80)
    description: Optional[str] = None
    score_delta: Optional[float] = 0.0


class AnnotationCreate(BaseModel):
    replay_id: int
    category: str
    note: str


@router.post("/start")
def start_replay(data: ReplayStart, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return crud.start_replay(db, data.model_dump(), user_id)


@router.get("/list")
def list_replays(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return crud.list_replays(db, user_id)


@router.post("/{replay_id}/complete")
def complete_replay(replay_id: int, data: ReplayComplete, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return crud.complete_replay(db, replay_id, user_id, data.score)


@router.get("/{replay_id}")
def get_replay(replay_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return crud.get_owned_replay(db, replay_id, user_id)


@router.post("/step")
def add_step(data: StepCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return crud.add_step(db, data.model_dump(), user_id)


@router.get("/step/{replay_id}")
def list_steps(replay_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return crud.list_steps(db, replay_id, user_id)


@router.post("/annotation")
def add_annotation(data: AnnotationCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return crud.add_annotation(db, data.model_dump(), user_id)


@router.get("/annotation/{replay_id}")
def list_annotations(replay_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return crud.list_annotations(db, replay_id, user_id)
