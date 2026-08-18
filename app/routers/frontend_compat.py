from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.crud.workout_log import create_workout_log
from app.database.connection import get_db
from app.models.daily_log import DailyLog
from app.models.user import User
from app.models.user_profile import UserProfile
from app.models.workout_log import WorkoutLog
from app.schemas.workout_log import WorkoutLogCreate
from app.utils.security import get_current_user_id

router = APIRouter(tags=["Frontend compatibility"])


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    dob: Optional[str] = None
    weight_unit: str = "kg"
    height_unit: str = "cm"
    starting_weight: Optional[str] = None
    current_weight: Optional[str] = None
    goal_weight: Optional[str] = None
    height: Optional[str] = None


class ProgressDailyInput(BaseModel):
    email: Optional[str] = None  # accepted for old clients; identity comes from JWT
    date: Optional[str] = None
    protein: float = 0
    water: float = 0
    calories: float = 0
    meals: float = 0
    workouts: float = 0
    supplements: float = 0


class FreeTrainingInput(BaseModel):
    workout_name: str
    skill_focus: Optional[str] = None
    notes: Optional[str] = None
    extra: Optional[str] = None
    duration_seconds: int = 0


class LegacyWorkoutInput(BaseModel):
    mode: str
    sport: Optional[str] = None
    category: Optional[str] = None
    level: Optional[str] = None
    drill: Any = None
    duration: Any = 0
    notes: Optional[str] = None
    timestamp: Optional[datetime] = None
    completed: bool = True


def _profile_payload(user: User, profile: Optional[UserProfile]) -> dict:
    return {
        "name": user.name,
        "dob": profile.dob if profile else None,
        "weight_unit": profile.weight_unit if profile else "kg",
        "height_unit": profile.height_unit if profile else "cm",
        "starting_weight": profile.starting_weight if profile else None,
        "current_weight": profile.current_weight if profile else None,
        "goal_weight": profile.goal_weight if profile else None,
        "height": profile.height if profile else None,
    }


def _daily_payload(log: DailyLog) -> dict:
    return {
        "id": log.id,
        "date": log.date.date().isoformat() if log.date else None,
        "protein": log.protein or 0,
        "water": log.water or 0,
        "calories": log.calories or 0,
        "meals": log.meals or 0,
        "workouts": log.workouts or 0,
        "supplements": log.supplements or 0,
    }


@router.get("/profile/get")
def get_profile(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    return _profile_payload(user, profile)


@router.post("/profile/update")
def update_profile(
    data: ProfileUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if data.name and data.name.strip():
        user.name = data.name.strip()

    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if profile is None:
        profile = UserProfile(user_id=user_id)
        db.add(profile)

    for field in ("dob", "weight_unit", "height_unit", "starting_weight", "current_weight", "goal_weight", "height"):
        setattr(profile, field, getattr(data, field))
    db.commit()
    db.refresh(profile)
    return {"success": True, **_profile_payload(user, profile)}


@router.post("/api/progress/log")
def save_progress_daily(
    data: ProgressDailyInput,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    try:
        day = datetime.fromisoformat(data.date).date() if data.date else datetime.utcnow().date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date")

    start = datetime.combine(day, datetime.min.time())
    end = start + timedelta(days=1)
    log = (
        db.query(DailyLog)
        .filter(DailyLog.user_id == user_id, DailyLog.date >= start, DailyLog.date < end)
        .first()
    )
    if log is None:
        log = DailyLog(user_id=user_id, date=start)
        db.add(log)

    for field in ("protein", "water", "calories", "meals", "workouts", "supplements"):
        setattr(log, field, getattr(data, field))
    db.commit()
    db.refresh(log)
    return {"success": True, "entry": _daily_payload(log)}


@router.get("/api/progress/history")
def progress_history(
    email: Optional[str] = Query(default=None),  # legacy query accepted, not trusted
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    logs = db.query(DailyLog).filter(DailyLog.user_id == user_id).order_by(DailyLog.date.asc()).all()
    return {"success": True, "history": [_daily_payload(log) for log in logs]}


@router.get("/api/progress/summary")
def progress_summary(
    days: int = Query(default=7, ge=1, le=3650),
    email: Optional[str] = Query(default=None),  # legacy query accepted, not trusted
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    cutoff = datetime.utcnow() - timedelta(days=days)
    logs = (
        db.query(DailyLog)
        .filter(DailyLog.user_id == user_id, DailyLog.date >= cutoff)
        .order_by(DailyLog.date.asc())
        .all()
    )
    return {"success": True, "entries": [_daily_payload(log) for log in logs]}


@router.post("/free/log")
def save_free_training(
    data: FreeTrainingInput,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    workout = WorkoutLogCreate(
        mode="manual",
        duration_minutes=max(0, round(data.duration_seconds / 60)),
        manual_name=data.workout_name,
        manual_notes=data.notes,
        plan_json={"skill_focus": data.skill_focus, "extra": data.extra, "duration_seconds": data.duration_seconds},
        timestamp=datetime.utcnow(),
    )
    return create_workout_log(db, user_id, workout)


@router.post("/workouts")
def save_legacy_workout(
    data: LegacyWorkoutInput,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    try:
        duration_minutes = int(float(data.duration or 0))
    except (TypeError, ValueError):
        duration_minutes = 0
    structured = data.mode != "manual"
    workout = WorkoutLogCreate(
        mode="structured" if structured else "manual",
        duration_minutes=max(0, duration_minutes),
        manual_name=None if structured else data.sport,
        manual_notes=data.notes,
        workout_type=data.sport if structured else None,
        plan_json={
            "category": data.category,
            "level": data.level,
            "drill": data.drill,
            "completed": data.completed,
        } if structured else None,
        timestamp=data.timestamp or datetime.utcnow(),
    )
    return create_workout_log(db, user_id, workout)


@router.get("/drills/recent")
def recent_drills(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    workouts = (
        db.query(WorkoutLog)
        .filter(WorkoutLog.user_id == user_id, WorkoutLog.mode == "structured")
        .order_by(WorkoutLog.date.desc())
        .limit(20)
        .all()
    )
    logs = []
    for workout in workouts:
        plan = workout.plan_json if isinstance(workout.plan_json, dict) else {}
        drill = plan.get("drill")
        if isinstance(drill, dict):
            output = drill.get("output") or drill.get("name") or str(drill)
        else:
            output = drill or workout.manual_notes or "Workout completed"
        logs.append(
            {
                "id": workout.id,
                "sport": workout.workout_type or workout.manual_name or "Training",
                "category": plan.get("category") or "General",
                "output": output,
                "timestamp": workout.date.isoformat() if workout.date else None,
            }
        )
    return {"logs": logs}
