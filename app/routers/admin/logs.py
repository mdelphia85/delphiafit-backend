from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.daily_log import DailyLog
from app.models.login_log import LoginLog
from app.models.sports_log import SportsLog
from app.models.user import User
from app.models.workout_log import WorkoutLog
from app.routers.admin.auth import verify_admin

router = APIRouter(prefix="/admin/logs", tags=["Admin Logs"])


def _email_map(db: Session) -> dict[int, str]:
    return {user.id: user.email for user in db.query(User).all()}


@router.get("")
def get_all_logs(
    type: str | None = Query(default=None),
    db: Session = Depends(get_db),
    admin=Depends(verify_admin),
):
    emails = _email_map(db)
    rows: list[dict] = []

    for log in db.query(WorkoutLog).order_by(WorkoutLog.date.desc()).limit(250).all():
        rows.append({
            "id": f"workout-{log.id}",
            "type": "workout",
            "message": f"Workout logged: {log.workout_type or log.manual_name or log.mode}",
            "user_email": emails.get(log.user_id),
            "timestamp": log.date.isoformat() if log.date else None,
        })
    for log in db.query(DailyLog).order_by(DailyLog.date.desc()).limit(250).all():
        rows.append({
            "id": f"daily-{log.id}",
            "type": "daily",
            "message": "Daily progress log saved",
            "user_email": emails.get(log.user_id),
            "timestamp": log.date.isoformat() if log.date else None,
        })
    for log in db.query(LoginLog).order_by(LoginLog.timestamp.desc()).limit(250).all():
        rows.append({
            "id": f"auth-{log.id}",
            "type": "auth",
            "message": "User login",
            "user_email": emails.get(log.user_id),
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
        })
    for log in db.query(SportsLog).order_by(SportsLog.date.desc()).limit(250).all():
        rows.append({
            "id": f"sports-{log.id}",
            "type": "workout",
            "message": f"Sports session logged: {log.sport}",
            "user_email": emails.get(log.user_id),
            "timestamp": log.date.isoformat() if log.date else None,
        })

    rows.sort(key=lambda item: item.get("timestamp") or "", reverse=True)
    if type and type != "all":
        rows = [row for row in rows if row["type"] == type]
    return {"logs": rows[:500]}
