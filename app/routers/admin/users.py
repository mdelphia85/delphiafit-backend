from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from datetime import datetime

from app.crud.user import delete_user as delete_user_record
from app.database.connection import get_db
from app.models.activity import ActivityLog
from app.models.daily_log import DailyLog
from app.models.login_log import LoginLog
from app.models.messages import Message
from app.models.user import User
from app.models.workout_log import WorkoutLog
from app.routers.admin.auth import record_audit, verify_admin
from app.schemas.user import AdminUserResponse

router = APIRouter(prefix="/admin/users", tags=["Admin Users"])


class SuspendBody(BaseModel):
    suspended: bool | None = None


class RoleBody(BaseModel):
    is_admin: bool


def _get_user(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def _admin_count(db: Session) -> int:
    return db.query(User).filter(User.is_admin.is_(True)).count()


def _serialize(user: User, last_login) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "is_admin": bool(user.is_admin),
        "is_suspended": bool(user.is_suspended),
        "streak": user.streak or 0,
        "created_at": user.created_at,
        "last_login": last_login,
    }


def _last_login(db: Session, user_id: int):
    row = (
        db.query(func.max(LoginLog.timestamp))
        .filter(LoginLog.user_id == user_id)
        .scalar()
    )
    return row


@router.get("", response_model=list[AdminUserResponse])
def get_all_users(
    q: str | None = Query(default=None, description="Case-insensitive match on name or email"),
    limit: int = Query(default=500, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    admin=Depends(verify_admin),
):
    query = db.query(User)
    if q and q.strip():
        like = f"%{q.strip().lower()}%"
        query = query.filter(or_(func.lower(User.email).like(like), func.lower(User.name).like(like)))
    users = query.order_by(User.id.desc()).offset(offset).limit(limit).all()

    last_logins = {}
    if users:
        rows = (
            db.query(LoginLog.user_id, func.max(LoginLog.timestamp))
            .filter(LoginLog.user_id.in_([u.id for u in users]))
            .group_by(LoginLog.user_id)
            .all()
        )
        last_logins = {user_id: ts for user_id, ts in rows}
    return [_serialize(u, last_logins.get(u.id)) for u in users]


@router.get("/{user_id}", response_model=AdminUserResponse)
def get_user(user_id: int, db: Session = Depends(get_db), admin=Depends(verify_admin)):
    user = _get_user(db, user_id)
    return _serialize(user, _last_login(db, user_id))


@router.get("/{user_id}/workouts")
def get_user_workouts(user_id: int, db: Session = Depends(get_db), admin=Depends(verify_admin)):
    _get_user(db, user_id)
    rows = (
        db.query(WorkoutLog)
        .filter(WorkoutLog.user_id == user_id)
        .order_by(WorkoutLog.date.desc())
        .limit(200)
        .all()
    )
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
    _get_user(db, user_id)
    rows = (
        db.query(DailyLog)
        .filter(DailyLog.user_id == user_id)
        .order_by(DailyLog.date.desc())
        .limit(200)
        .all()
    )
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
    user = _get_user(db, user_id)
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
    _get_user(db, user_id)
    results = []
    for row in db.query(ActivityLog).filter(ActivityLog.user_id == user_id).order_by(ActivityLog.date.desc()).limit(200).all():
        results.append({
            "id": f"activity-{row.id}",
            "timestamp": row.date.isoformat() if row.date else None,
            "message": f"{row.activity_type} ({row.duration_minutes} min)",
        })
    for row in db.query(LoginLog).filter(LoginLog.user_id == user_id).order_by(LoginLog.timestamp.desc()).limit(200).all():
        results.append({
            "id": f"login-{row.id}",
            "timestamp": row.timestamp.isoformat() if row.timestamp else None,
            "message": "User login",
        })
    results.sort(key=lambda item: item.get("timestamp") or "", reverse=True)
    return results


@router.patch("/{user_id}/reset-streak")
def reset_streak(user_id: int, db: Session = Depends(get_db), admin=Depends(verify_admin)):
    user = _get_user(db, user_id)
    previous = user.streak or 0
    user.streak = 0
    db.commit()
    db.refresh(user)
    record_audit(db, admin, "user.reset_streak", "user", user_id, f"{user.email}: streak {previous} -> 0")
    return {"status": "success", "user": _serialize(user, _last_login(db, user_id))}


def _set_admin(db: Session, admin: dict, user: User, make_admin: bool) -> dict:
    if user.is_admin == make_admin:
        return {"status": "success", "user": _serialize(user, _last_login(db, user.id))}
    if not make_admin:
        if user.id == admin["admin_id"]:
            raise HTTPException(status_code=400, detail="You cannot revoke your own admin access")
        if _admin_count(db) <= 1:
            raise HTTPException(status_code=400, detail="Cannot remove the last admin")
    user.is_admin = make_admin
    db.commit()
    db.refresh(user)
    record_audit(
        db, admin, "user.grant_admin" if make_admin else "user.revoke_admin",
        "user", user.id, user.email,
    )
    return {"status": "success", "user": _serialize(user, _last_login(db, user.id))}


@router.patch("/{user_id}/admin")
def toggle_admin(user_id: int, db: Session = Depends(get_db), admin=Depends(verify_admin)):
    user = _get_user(db, user_id)
    return _set_admin(db, admin, user, not user.is_admin)


@router.put("/{user_id}/role")
def set_role(user_id: int, body: RoleBody, db: Session = Depends(get_db), admin=Depends(verify_admin)):
    user = _get_user(db, user_id)
    return _set_admin(db, admin, user, body.is_admin)


@router.patch("/{user_id}/suspend")
def suspend_user(
    user_id: int,
    body: SuspendBody | None = None,
    db: Session = Depends(get_db),
    admin=Depends(verify_admin),
):
    user = (
        db.query(User)
        .filter(User.id == user_id)
        .with_for_update()
        .populate_existing()
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    target = body.suspended if body and body.suspended is not None else not user.is_suspended
    if target and user.id == admin["admin_id"]:
        raise HTTPException(status_code=400, detail="You cannot suspend your own account")
    if target and user.is_admin and _admin_count(db) <= 1:
        raise HTTPException(status_code=400, detail="Cannot suspend the last admin")
    if user.is_suspended != target:
        user.token_version = User.token_version + 1
    user.is_suspended = target
    user.suspended_at = datetime.utcnow() if target else None
    db.commit()
    db.refresh(user)
    record_audit(db, admin, "user.suspend" if target else "user.unsuspend", "user", user.id, user.email)
    return {"status": "success", "user": _serialize(user, _last_login(db, user_id))}


@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), admin=Depends(verify_admin)):
    user = _get_user(db, user_id)
    if user.id == admin["admin_id"]:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")
    if user.is_admin and _admin_count(db) <= 1:
        raise HTTPException(status_code=400, detail="Cannot delete the last admin")
    email = user.email
    delete_user_record(db, user_id)
    record_audit(db, admin, "user.delete", "user", user_id, email)
    return {"status": "deleted", "id": user_id}
