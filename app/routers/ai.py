from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from app.services.ai_engine import AIEngine

router = APIRouter(prefix="/ai", tags=["AI"])
ai = AIEngine()


# ---------------------------------------------------------
# Request Models
# ---------------------------------------------------------

class UserData(BaseModel):
    experience: str | None = None
    fatigue: int | None = None
    sleep_hours: float | None = None
    nutrition_score: int | None = None
    recent_volume: int | None = None
    recent_intensity: int | None = None
    rest_days_last_week: int | None = None
    goals: list[str] | None = None
    injuries: list[str] | None = None
    preferences: Dict[str, Any] | None = None
    sessions_per_week: int | None = None


class CoachRequest(BaseModel):
    user_data: Dict[str, Any]
    message: str


class MotionData(BaseModel):
    keypoints: list[Dict[str, Any]]
    reps: list[Dict[str, int]]
    exercise: str


class VelocityData(BaseModel):
    positions: list[Dict[str, Any]]
    timestamps: list[float]
    load: float
    exercise: str


# ---------------------------------------------------------
# AI Coach Chat
# ---------------------------------------------------------
@router.post("/coach")
def ai_coach(req: CoachRequest):
    try:
        return ai.coach(req.user_data, req.message)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Personalization
# ---------------------------------------------------------
@router.post("/personalize")
def ai_personalize(user_data: UserData):
    try:
        return ai.personalize(user_data.dict(exclude_none=True))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Smart Mode
# ---------------------------------------------------------
@router.post("/smart-mode")
def ai_smart_mode(user_data: UserData):
    try:
        return ai.smart_mode_adjust(user_data.dict(exclude_none=True))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Weekly Plan
# ---------------------------------------------------------
@router.post("/weekly-plan")
def ai_weekly_plan(user_data: UserData):
    try:
        return ai.generate_weekly_plan(user_data.dict(exclude_none=True))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Form Scoring
# ---------------------------------------------------------
@router.post("/form-score")
def ai_form_score(motion_data: MotionData):
    try:
        return ai.score_form(motion_data.dict())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Velocity Estimation
# ---------------------------------------------------------
@router.post("/velocity")
def ai_velocity(rep_data: VelocityData):
    try:
        return ai.estimate_velocity(rep_data.dict())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
