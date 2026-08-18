from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud.user import delete_user as delete_user_record
from app.database.connection import get_db
from app.models.user import User
from app.models.workout_log import WorkoutLog
from app.models.daily_log import DailyLog
from app.models.messages import Message
from app.models.login_log import LoginLog
from app.models.activity import ActivityLog
from app.routers.admin.auth import verify_admin
from app.schemas.user import AdminUserResponse

router = APIRouter(prefix="/admin/users", tags=["Admin Users"])


@router.get("", response_model=list[AdminUserResponse])
def get_all_users(
    db: Session = Depends(get_db),
    admin=Depends(verify_admin),
):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.get("/{user_id}", response_model=AdminUserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin=Depends(verify_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    last_login = (
        db.query(LoginLog)
        .filter(LoginLog.user_id == user_id)
        .order_by(LoginLog.timestamp.desc())
        .first()
    )
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "is_admin": user.is_admin,
        "streak": user.streak,
        "created_at": user.created_at,
        "last_login": last_login.timestamp if last_login else None,
    }


@router.get("/{user_id}/workouts")
def get_user_workouts(user_id: int, db: Session = Depends(get_db), admin=Depends(verify_admin)):
    rows = db.query(WorkoutLog).filter(WorkoutLog.user_id == user_id).order_by(WorkoutLog.date.desc()).all()
    return [
        {
            "id": row.id,
            "type": row.workout_type or row.manual_name or row.mode,
            "date": row.date.isoformat() if row.date else None,
        }
        for row in rows
    ]


@router.get("/{user_id}/daily")
def get_user_daily(user_id: int, db: Session = Depends(get_db), admin=Depends(verify_admin)):
    rows = db.query(DailyLog).filter(DailyLog.user_id == user_id).order_by(DailyLog.date.desc()).all()
    results = []
    for row in rows:
        parts = []
        if row.mood:
            parts.append(f"Mood: {row.mood}")
        if row.energy:
            parts.append(f"Energy: {row.energy}")
        if any((row.protein, row.water, row.calories, row.meals, row.workouts, row.supplements)):
            parts.append(f"Calories {row.calories or 0}, protein {row.protein or 0}, water {row.water or 0}")
        results.append({
            "id": row.id,
            "date": row.date.isoformat() if row.date else None,
            "summary": "; ".join(parts) or "Daily log",
        })
    return results


@router.get("/{user_id}/messages")
def get_user_messages(user_id: int, db: Session = Depends(get_db), admin=Depends(verify_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    rows = db.query(Message).filter(Message.email == user.email).order_by(Message.created_at.desc()).all()
    return [
        {
            "id": row.id,
            "date": row.created_at.isoformat() if row.created_at else None,
            "message": row.message,
        }
        for row in rows
    ]


@router.get("/{user_id}/logs")
def get_user_activity(user_id: int, db: Session = Depends(get_db), admin=Depends(verify_admin)):
    results = []
    for row in db.query(ActivityLog).filter(ActivityLog.user_id == user_id).order_by(ActivityLog.date.desc()).all():
        results.append({
            "id": f"activity-{row.id}",
            "timestamp": row.date.isoformat() if row.date else None,
            "message": f"{row.activity_type} ({row.duration_minutes} min)",
        })
    for row in db.query(LoginLog).filter(LoginLog.user_id == user_id).order_by(LoginLog.timestamp.desc()).all():
        results.append({
            "id": f"login-{row.id}",
            "timestamp": row.timestamp.isoformat() if row.timestamp else None,
            "message": "User login",
        })
    results.sort(key=lambda item: item.get("timestamp") or "", reverse=True)
    return results


@router.patch("/{user_id}/reset-streak")
def reset_streak(
    user_id: int,
    db: Session = Depends(get_db),
    admin=Depends(verify_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.streak = 0
    db.commit()
    db.refresh(user)
    return {"status": "success", "user": AdminUserResponse.model_validate(user)}


@router.patch("/{user_id}/admin")
def toggle_admin(
    user_id: int,
    db: Session = Depends(get_db),
    admin=Depends(verify_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_admin = not user.is_admin
    db.commit()
    db.refresh(user)
    return {"status": "success", "user": AdminUserResponse.model_validate(user)}


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin=Depends(verify_admin),
):
    if not db.query(User).filter(User.id == user_id).first():
        raise HTTPException(status_code=404, detail="User not found")

    delete_user_record(db, user_id)
    return {"status": "deleted", "id": user_id}
