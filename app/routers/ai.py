import json
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.ai_record import AIRecord
from app.services.ai_engine import AIEngine
from app.utils.security import get_current_user_id

router = APIRouter(prefix="/ai", tags=["AI"])
ai = AIEngine()


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


@router.get("/records")
def list_records(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    rows = db.query(AIRecord).filter(AIRecord.user_id == user_id).order_by(AIRecord.id.desc()).limit(50).all()
    return [_record_response(row) for row in rows]


@router.post("/coach")
def ai_coach(req: CoachRequest, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    try:
        result = ai.coach(req.user_data, req.message)
        row = _save(db, user_id, "coach", req.model_dump(), result)
        return {**result, "record_id": row.id}
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/personalize")
def ai_personalize(user_data: UserData, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    try:
        inputs = user_data.model_dump(exclude_none=True); result = ai.personalize(inputs)
        row = _save(db, user_id, "personalize", inputs, result)
        return {"result": result, "record_id": row.id}
    except Exception as exc:
        db.rollback(); raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/smart-mode")
def ai_smart_mode(user_data: UserData, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    try:
        inputs = user_data.model_dump(exclude_none=True); result = ai.smart_mode_adjust(inputs)
        row = _save(db, user_id, "smart-mode", inputs, result)
        return {"result": result, "record_id": row.id}
    except Exception as exc:
        db.rollback(); raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/weekly-plan")
def ai_weekly_plan(user_data: UserData, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    try:
        inputs = user_data.model_dump(exclude_none=True); result = ai.generate_weekly_plan(inputs)
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
