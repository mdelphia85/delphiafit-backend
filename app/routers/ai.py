import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.ai_record import AIRecord
from app.models.workout_log import WorkoutLog
from app.services.ai_engine import AIEngine
from app.services import conversational_coach
from app.utils.security import get_current_user_id

router = APIRouter(prefix="/ai", tags=["AI"])
ai = AIEngine()
logger = logging.getLogger(__name__)

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


def _save(
    db: Session,
    user_id: int,
    feature: str,
    inputs: dict,
    result: dict,
    idempotency_key: str | None = None,
):
    row = AIRecord(
        user_id=user_id,
        feature=feature,
        idempotency_key=idempotency_key,
        input_json=json.dumps(inputs, default=str),
        result_json=json.dumps(result, default=str),
    )
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        if idempotency_key is None:
            raise
        existing = db.query(AIRecord).filter(
            AIRecord.user_id == user_id,
            AIRecord.feature == "coach",
            AIRecord.idempotency_key == idempotency_key,
        ).first()
        if existing is None:
            raise
        return existing
    db.refresh(row)
    return row


def _record_response(row: AIRecord):
    return {"id": row.id, "feature": row.feature, "input": json.loads(row.input_json), "result": json.loads(row.result_json), "created_at": row.created_at}


def _same_coach_request(row: AIRecord, request_payload: dict) -> bool:
    stored_input = json.loads(row.input_json)
    original_request = stored_input.get("request_payload")
    if original_request is not None:
        return json.dumps(original_request, sort_keys=True, separators=(",", ":")) == json.dumps(
            request_payload, sort_keys=True, separators=(",", ":")
        )
    stored_message = stored_input.get("message")
    stored_user_data = stored_input.get("user_data", {})
    return (
        stored_message == request_payload["message"]
        and all(stored_user_data.get(key) == value for key, value in request_payload["user_data"].items())
    )


def _idempotency_conflict() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Idempotency key was already used for a different request.",
    )


def _raise_ai_failure(
    db: Session,
    operation: str,
    user_id: int,
    exc: Exception,
    public_message: str,
) -> None:
    try:
        db.rollback()
    except Exception as rollback_exc:
        logger.error(
            "AI %s rollback failed for user %s (exception type: %s)",
            operation,
            user_id,
            type(rollback_exc).__name__,
        )
    logger.error(
        "AI %s failed for user %s (exception type: %s)",
        operation,
        user_id,
        type(exc).__name__,
    )
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=public_message) from None


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
        # The number of workouts recorded on this platform does not establish\n        # actual training experience. Leave it unknown unless explicitly supplied\n        # or already saved as an adaptive difficulty preference.
    categories = {
        key: value for key, value in (profile.get("preferredCategories") or {}).items()
        if isinstance(key, str) and key.strip() and key.strip().lower() not in {"undefined", "null"}
        and isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0
    }
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
    try:
        return {"profile": _stored_profile(db, user_id)}
    except Exception as exc:
        _raise_ai_failure(db, "profile read", user_id, exc, "Unable to load your coaching profile.")


@router.put("/profile")
def save_adaptive_profile(profile: AdaptiveProfile, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    payload = profile.model_dump(exclude_none=True)
    try:
        row = db.query(AIRecord).filter(AIRecord.user_id == user_id, AIRecord.feature == PROFILE_FEATURE).order_by(AIRecord.id.desc()).first()
        if row:
            row.input_json = json.dumps(payload)
            row.result_json = "{}"
            row.created_at = datetime.utcnow()
        else:
            row = AIRecord(user_id=user_id, feature=PROFILE_FEATURE, input_json=json.dumps(payload), result_json="{}")
            db.add(row)
        db.commit()
    except Exception as exc:
        _raise_ai_failure(db, "profile save", user_id, exc, "Unable to save your coaching profile.")
    return {"profile": payload}


@router.get("/records")
def list_records(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    try:
        rows = db.query(AIRecord).filter(AIRecord.user_id == user_id, AIRecord.feature != PROFILE_FEATURE).order_by(AIRecord.id.desc()).limit(50).all()
        return [_record_response(row) for row in rows]
    except Exception as exc:
        _raise_ai_failure(db, "records read", user_id, exc, "Unable to load your coaching history.")


@router.post("/coach")
def ai_coach(
    req: CoachRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    if not req.message.strip() or len(req.message) > 4000:
        raise HTTPException(status_code=422, detail="Question must be 1-4000 characters")
    request_payload = {"user_data": req.user_data, "message": req.message}
    try:
        if idempotency_key is not None:
            idempotency_key = idempotency_key.strip()
            if not idempotency_key or len(idempotency_key) > 128:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid idempotency key")
            existing = db.query(AIRecord).filter(
                AIRecord.user_id == user_id,
                AIRecord.feature == "coach",
                AIRecord.idempotency_key == idempotency_key,
            ).first()
            if existing is not None:
                if not _same_coach_request(existing, request_payload):
                    raise _idempotency_conflict()
                return {**json.loads(existing.result_json), "record_id": existing.id}

        user_data, used = _adapt(db, user_id, req.user_data)
        if conversational_coach.is_conversational_coach_configured():
            earlier = (
                db.query(AIRecord)
                .filter(AIRecord.user_id == user_id, AIRecord.feature == "coach")
                .order_by(AIRecord.id.desc())
                .limit(6)
                .all()
            )
            prior = []
            for item in reversed(earlier):
                try:
                    prior_input = json.loads(item.input_json)
                    prior_result = json.loads(item.result_json)
                    prior.append({
                        "message": prior_input.get("message", ""),
                        "answer": prior_result.get("coach_response", ""),
                    })
                except (TypeError, ValueError):
                    continue
            result = {
                "coach_response": conversational_coach.respond(
                    req.message, user_data, used, prior
                ),
                "mode": "conversational",
            }
        else:
            # Keep existing functionality working until an API key is
            # configured. The UI must disclose that this is a limited mode.
            result = ai.coach(user_data, req.message)
            result["mode"] = "limited"
        result["adaptive_inputs"] = used
        row = _save(
            db,
            user_id,
            "coach",
            {"user_data": user_data, "message": req.message, "request_payload": request_payload},
            result,
            idempotency_key=idempotency_key,
        )
        if idempotency_key is not None and not _same_coach_request(row, request_payload):
            raise _idempotency_conflict()
        return {**json.loads(row.result_json), "record_id": row.id}
    except HTTPException:
        raise
    except Exception as exc:
        _raise_ai_failure(db, "coach request", user_id, exc, "Unable to prepare coaching guidance.")


@router.post("/personalize")
def ai_personalize(user_data: UserData, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    try:
        inputs, used = _adapt(db, user_id, user_data.model_dump(exclude_none=True)); result = ai.personalize(inputs)
        result["adaptive_inputs"] = used
        row = _save(db, user_id, "personalize", inputs, result)
        return {"result": result, "record_id": row.id}
    except Exception as exc:
        _raise_ai_failure(db, "personalize", user_id, exc, "Unable to personalize your workout.")


@router.post("/smart-mode")
def ai_smart_mode(user_data: UserData, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    try:
        inputs, used = _adapt(db, user_id, user_data.model_dump(exclude_none=True)); result = ai.smart_mode_adjust(inputs)
        result["adaptive_inputs"] = used
        row = _save(db, user_id, "smart-mode", inputs, result)
        return {"result": result, "record_id": row.id}
    except Exception as exc:
        _raise_ai_failure(db, "smart mode", user_id, exc, "Unable to adjust your workout.")


@router.post("/weekly-plan")
def ai_weekly_plan(user_data: UserData, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    try:
        inputs, used = _adapt(db, user_id, user_data.model_dump(exclude_none=True)); result = ai.generate_weekly_plan(inputs)
        result["adaptive_inputs"] = used
        row = _save(db, user_id, "weekly-plan", inputs, result)
        return {"result": result, "record_id": row.id}
    except Exception as exc:
        _raise_ai_failure(db, "weekly plan", user_id, exc, "Unable to prepare your weekly plan.")


@router.post("/form-score")
def ai_form_score(motion_data: MotionData, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    try:
        inputs = motion_data.model_dump(); result = ai.score_form(inputs)
        row = _save(db, user_id, "form-score", inputs, result)
        return {"result": result, "record_id": row.id}
    except Exception as exc:
        _raise_ai_failure(db, "form score", user_id, exc, "Unable to score exercise form.")


@router.post("/velocity")
def ai_velocity(rep_data: VelocityData, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    try:
        inputs = rep_data.model_dump(); result = ai.estimate_velocity(inputs)
        row = _save(db, user_id, "velocity", inputs, result)
        return {"result": result, "record_id": row.id}
    except Exception as exc:
        _raise_ai_failure(db, "velocity", user_id, exc, "Unable to estimate movement velocity.")
