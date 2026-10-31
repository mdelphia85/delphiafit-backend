from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.services.live_sync import LiveSyncService
from app.services.rep_counter import RepCounterService
from app.services.video_ai import VideoAIService
from app.utils.security import get_current_user_id

router = APIRouter(prefix="/live", tags=["live"])
live_sync = LiveSyncService()
rep_counter = RepCounterService()
video_ai = VideoAIService()


class LiveClassJoin(BaseModel):
    class_id: int


class CoachingStart(BaseModel):
    coach_id: int


class RepStream(BaseModel):
    movement: str
    frame_data: Dict[str, Any]


class VideoRequest(BaseModel):
    video_url: str
    mode: str


class OfflineSync(BaseModel):
    payload: Dict[str, Any]


@router.post("/class/join")
def join_class(data: LiveClassJoin, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return live_sync.join_class(db, {**data.model_dump(), "user_id": user_id})


@router.post("/coaching/start")
def start_coaching(data: CoachingStart, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return live_sync.start_coaching(db, {**data.model_dump(), "user_id": user_id})


@router.post("/reps/stream")
def stream_reps(data: RepStream, user_id: int = Depends(get_current_user_id)):
    return rep_counter.process_frame({**data.model_dump(), "user_id": user_id})


@router.post("/video/request")
def video_ai_request(data: VideoRequest, user_id: int = Depends(get_current_user_id)):
    return video_ai.process_request({**data.model_dump(), "user_id": user_id})


@router.post("/sync/offline")
def offline_sync(data: OfflineSync, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return live_sync.sync_offline(db, {**data.model_dump(), "user_id": user_id})
