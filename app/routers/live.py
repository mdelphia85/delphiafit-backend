from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.database.connection import get_db
from app.services.live_sync import LiveSyncService
from app.services.rep_counter import RepCounterService
from app.services.video_ai import VideoAIService

router = APIRouter(prefix="/live", tags=["live"])

live_sync = LiveSyncService()
rep_counter = RepCounterService()
video_ai = VideoAIService()


# ---------------------------------------------------------
# Schemas
# ---------------------------------------------------------

class LiveClassJoin(BaseModel):
    user_id: int
    class_id: int


class CoachingStart(BaseModel):
    user_id: int
    coach_id: int


class RepStream(BaseModel):
    user_id: int
    movement: str
    frame_data: Dict[str, Any]  # keypoints, velocity, angles


class VideoRequest(BaseModel):
    user_id: int
    video_url: str
    mode: str  # breakdown, highlight, commentary


class OfflineSync(BaseModel):
    user_id: int
    payload: Dict[str, Any]


# ---------------------------------------------------------
# Live Classes
# ---------------------------------------------------------
@router.post("/class/join")
def join_class(data: LiveClassJoin, db: Session = Depends(get_db)):
    return live_sync.join_class(db, data.dict())


# ---------------------------------------------------------
# Live Coaching
# ---------------------------------------------------------
@router.post("/coaching/start")
def start_coaching(data: CoachingStart, db: Session = Depends(get_db)):
    return live_sync.start_coaching(db, data.dict())


# ---------------------------------------------------------
# Real-Time Rep Counting
# ---------------------------------------------------------
@router.post("/reps/stream")
def stream_reps(data: RepStream):
    return rep_counter.process_frame(data.dict())


# ---------------------------------------------------------
# Video AI (Breakdowns, Highlights, Commentary)
# ---------------------------------------------------------
@router.post("/video/request")
def video_ai_request(data: VideoRequest):
    return video_ai.process_request(data.dict())


# ---------------------------------------------------------
# Offline Sync
# ---------------------------------------------------------
@router.post("/sync/offline")
def offline_sync(data: OfflineSync, db: Session = Depends(get_db)):
    return live_sync.sync_offline(db, data.dict())
