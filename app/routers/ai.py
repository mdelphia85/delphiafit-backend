import json
from datetime import datetime, timedelta
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.ai_record import AIRecord
from app.models.workout_log import WorkoutLog
from app.services.ai_engine import AIEngine
from app.utils.security import get_current_user_id

router = APIRouter(prefix="/ai", tags=["AI"])
ai = AIEngine()

PROFILE_FEATURE = "adaptive-profile"
DIFFICULTY_TO_EXPERIENCE = {"easy": "beginner", "medium": "intermediate", "hard": "advanced"}
CATEGORY_TO_GOAL = {"strength": "strength", "cardio": "endurance", "endurance": "endurance", "conditioning": "fat_loss", "hypertrophy": "muscle_gain"}


class AdaptiveProfile(BaseModel):
    completionRate: float | None = None
    avgIntensity: float | None = None
    avgDurationAccuracy: float | None = None
    preferredCategories: Dict[str, float] | None = None
    preferredTimes: Dict[str, float] | None = None
    difficulty: str | None = None


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


def _save(db: Session, user_id: int, feature: str, inputs: dict, result: dict):
    row = AIRecord(user_id=user_id, feature=feature, input_json=json.dumps(inputs, default=str), result_json=json.dumps(result, default=str))
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _record_response(row: AIRecord):
    return {"id": row.id, "feature": row.feature, "input": json.loads(row.input_json), "result": json.loads(row.result_json), "created_at": row.created_at}


def _stored_profile(db: Session, user_id: int) -> dict | None:
    row = db.query(AIRecord).filter(AIRecord.user_id == user_id, AIRecord.feature == PROFILE_FEATURE).order_by(AIRecord.id.desc()).first()
    return json.loads(row.input_json) if row else None


def _adapt(db: Session, user_id: int, data: dict) -> tuple[dict, dict]:
    """Fill gaps in the request from the user's real workout history and saved adaptive profile.
    Values the client sends explicitly always win."""
    adapted = dict(data)
    used: dict = {}
    now = datetime.utcnow()
    logs = db.query(WorkoutLog.date).filter(WorkoutLog.user_id == user_id).all()
    week = [d for (d,) in logs if d and d >= now - timedelta(days=7)]
    if logs:
        used["workouts_logged"] = len(logs)
        used["workouts_last_7_days"] = len(week)
        if adapted.get("recent_volume") is None:
            adapted["recent_volume"] = len(week) * 20
        if adapted.get("rest_days_last_week") is None:
            adapted["rest_days_last_week"] = max(0, 7 - len({d.date() for d in week}))
    profile = _stored_profile(db, user_id) or {}
    if adapted.get("experience") is None:
        if profile.get("difficulty") in DIFFICULTY_TO_EXPERIENCE:
            adapted["experience"] = DIFFICULTY_TO_EXPERIENCE[profile["difficulty"]]
            used["difficulty"] = profile["difficulty"]
        elif logs:
            adapted["experience"] = "beginner" if len(logs) < 10 else "intermediate" if len(logs) < 50 else "advanced"
    categories = profile.get("preferredCategories") or {}
    if categories:
        top = max(categories, key=categories.get)
        used["preferred_category"] = top
        adapted["preferences"] = {**(adapted.get("preferences") or {}), "preferred_category": top}
        goal = next((g for key, g in CATEGORY_TO_GOAL.items() if key in str(top).lower()), None)
        if goal and not adapted.get("goals"):
            adapted["goals"] = [goal]
    if adapted.get("recent_intensity") is None and profile.get("avgIntensity"):
        adapted["recent_intensity"] = round(profile["avgIntensity"] * 10)
    return adapted, used


@router.get("/profile")
def get_adaptive_profile(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return {"profile": _stored_profile(db, user_id)}


@router.put("/profile")
def save_adaptive_profile(profile: AdaptiveProfile, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    payload = profile.model_dump(exclude_none=True)
    row = db.query(AIRecord).filter(AIRecord.user_id == user_id, AIRecord.feature == PROFILE_FEATURE).order_by(AIRecord.id.desc()).first()
    if row:
        row.input_json = json.dumps(payload)
        row.result_json = "{}"
        row.created_at = datetime.utcnow()
    else:
        row = AIRecord(user_id=user_id, feature=PROFILE_FEATURE, input_json=json.dumps(payload), result_json="{}")
        db.add(row)
    db.commit()
    return {"profile": payload}


@router.get("/records")
def list_records(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    rows = db.query(AIRecord).filter(AIRecord.user_id == user_id, AIRecord.feature != PROFILE_FEATURE).order_by(AIRecord.id.desc()).limit(50).all()
    return [_record_response(row) for row in rows]


@router.post("/coach")
def ai_coach(req: CoachRequest, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    try:
        user_data, used = _adapt(db, user_id, req.user_data)
        result = ai.coach(user_data, req.message)
        result["adaptive_inputs"] = used
        row = _save(db, user_id, "coach", {"user_data": user_data, "message": req.message}, result)
        return {**result, "record_id": row.id}
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/personalize")
def ai_personalize(user_data: UserData, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    try:
        inputs, used = _adapt(db, user_id, user_data.model_dump(exclude_none=True)); result = ai.personalize(inputs)
        result["adaptive_inputs"] = used
        row = _save(db, user_id, "personalize", inputs, result)
        return {"result": result, "record_id": row.id}
    except Exception as exc:
        db.rollback(); raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/smart-mode")
def ai_smart_mode(user_data: UserData, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    try:
        inputs, used = _adapt(db, user_id, user_data.model_dump(exclude_none=True)); result = ai.smart_mode_adjust(inputs)
        result["adaptive_inputs"] = used
        row = _save(db, user_id, "smart-mode", inputs, result)
        return {"result": result, "record_id": row.id}
    except Exception as exc:
        db.rollback(); raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/weekly-plan")
def ai_weekly_plan(user_data: UserData, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    try:
        inputs, used = _adapt(db, user_id, user_data.model_dump(exclude_none=True)); result = ai.generate_weekly_plan(inputs)
        result["adaptive_inputs"] = used
        row = _save(db, user_id, "weekly-plan", inputs, result)
        return {"result": result, "record_id": row.id}
    except Exception as exc:
        db.rollback(); raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/form-score")
def ai_form_score(motion_data: MotionData, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    try:
        inputs = motion_data.model_dump(); result = ai.score_form(inputs)
        row = _save(db, user_id, "form-score", inputs, result)
        return {"result": result, "record_id": row.id}
    except Exception as exc:
        db.rollback(); raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/velocity")
def ai_velocity(rep_data: VelocityData, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    try:
        inputs = rep_data.model_dump(); result = ai.estimate_velocity(inputs)
        row = _save(db, user_id, "velocity", inputs, result)
        return {"result": result, "record_id": row.id}
    except Exception as exc:
        db.rollback(); raise HTTPException(status_code=400, detail=str(exc)) from exc
