from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.daily_log import DailyLog
from app.models.login_log import LoginLog
from app.models.logs import AdminAuditLog
from app.models.sports_log import SportsLog
from app.models.user import User
from app.models.workout_log import WorkoutLog
from app.routers.admin.auth import verify_admin

router = APIRouter(prefix="/admin/logs", tags=["Admin Logs"])

LOG_TYPES = {"auth", "workout", "daily", "system", "error"}


def _iso(value):
    return value.isoformat() if value else None


@router.get("")
def get_all_logs(
    type: str | None = Query(default=None, description="auth | workout | daily | system | error | all"),
    limit: int = Query(default=500, ge=1, le=1000),
    db: Session = Depends(get_db),
    admin=Depends(verify_admin),
):
    """Unified, newest-first log feed built from real tables.

    auth = user logins, workout = workout/sports logs, daily = daily logs,
    system = admin audit entries, error = failed admin actions (e.g. bad admin login).
    """
    wanted = type if type in LOG_TYPES else None
    per_source = limit
    rows: list[dict] = []
    user_ids: set[int] = set()

    def add(items, make):
        for item in items:
            row = make(item)
            rows.append(row)
            if row.get("_uid") is not None:
                user_ids.add(row["_uid"])

    if wanted in (None, "workout"):
        add(
            db.query(WorkoutLog).order_by(WorkoutLog.date.desc()).limit(per_source).all(),
            lambda log: {
                "id": f"workout-{log.id}", "type": "workout",
                "message": f"Workout logged: {log.workout_type or log.manual_name or log.mode}",
                "_uid": log.user_id, "timestamp": _iso(log.date),
            },
        )
        add(
            db.query(SportsLog).order_by(SportsLog.date.desc()).limit(per_source).all(),
            lambda log: {
                "id": f"sports-{log.id}", "type": "workout",
                "message": f"Sports session logged: {log.sport}",
                "_uid": log.user_id, "timestamp": _iso(log.date),
            },
        )
    if wanted in (None, "daily"):
        add(
            db.query(DailyLog).order_by(DailyLog.date.desc()).limit(per_source).all(),
            lambda log: {
                "id": f"daily-{log.id}", "type": "daily", "message": "Daily progress log saved",
                "_uid": log.user_id, "timestamp": _iso(log.date),
            },
        )
    if wanted in (None, "auth"):
        add(
            db.query(LoginLog).order_by(LoginLog.timestamp.desc()).limit(per_source).all(),
            lambda log: {
                "id": f"auth-{log.id}", "type": "auth", "message": "User login",
                "_uid": log.user_id, "timestamp": _iso(log.timestamp),
            },
        )
    if wanted in (None, "system", "error"):
        query = db.query(AdminAuditLog)
        if wanted == "system":
            query = query.filter(AdminAuditLog.success.is_(True))
        elif wanted == "error":
            query = query.filter(AdminAuditLog.success.is_(False))
        for log in query.order_by(AdminAuditLog.created_at.desc()).limit(per_source).all():
            label = log.action + (f" {log.target_type}#{log.target_id}" if log.target_type else "")
            if log.detail:
                label += f" - {log.detail}"
            rows.append({
                "id": f"audit-{log.id}",
                "type": "system" if log.success else "error",
                "message": label,
                "user_email": log.admin_email,
                "timestamp": _iso(log.created_at),
            })

    emails = (
        {u.id: u.email for u in db.query(User).filter(User.id.in_(user_ids)).all()} if user_ids else {}
    )
    for row in rows:
        uid = row.pop("_uid", None)
        if uid is not None:
            row["user_email"] = emails.get(uid)

    rows.sort(key=lambda item: item.get("timestamp") or "", reverse=True)
    return {"logs": rows[:limit]}
