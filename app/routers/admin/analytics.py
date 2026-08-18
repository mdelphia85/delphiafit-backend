from collections import Counter
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.daily_log import DailyLog
from app.models.login_log import LoginLog
from app.models.user import User
from app.models.workout_log import WorkoutLog
from app.routers.admin.auth import verify_admin

router = APIRouter(prefix="/admin/analytics", tags=["Admin Analytics"])


@router.get("")
def get_admin_analytics(db: Session = Depends(get_db), admin=Depends(verify_admin)):
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    users = db.query(User).all()
    email_by_id = {user.id: user.email for user in users}

    workouts = db.query(WorkoutLog).filter(WorkoutLog.date >= week_ago).all()
    daily_logs = db.query(DailyLog).filter(DailyLog.date >= week_ago).all()
    logins = db.query(LoginLog).filter(LoginLog.timestamp >= week_ago).all()

    active_ids = {row.user_id for row in workouts} | {row.user_id for row in daily_logs} | {row.user_id for row in logins}
    names = Counter((row.workout_type or row.manual_name or row.mode or "Workout") for row in workouts)
    top_workouts = [{"label": label, "count": count} for label, count in names.most_common(8)]

    activity = []
    for row in workouts:
        activity.append({
            "id": f"workout-{row.id}", "type": "workout",
            "detail": row.workout_type or row.manual_name or "Workout logged",
            "user": email_by_id.get(row.user_id, "Unknown user"),
            "time": row.date.isoformat() if row.date else None,
        })
    for row in daily_logs:
        activity.append({
            "id": f"daily-{row.id}", "type": "daily", "detail": "Daily log saved",
            "user": email_by_id.get(row.user_id, "Unknown user"),
            "time": row.date.isoformat() if row.date else None,
        })
    activity.sort(key=lambda item: item.get("time") or "", reverse=True)

    overview = {
        "totalUsers": len(users),
        "activeUsers7d": len(active_ids),
        "workoutsLogged7d": len(workouts),
        "dailyLogs7d": len(daily_logs),
    }
    return {
        "overview": overview,
        "top_workouts": top_workouts,
        "recent_activity": activity[:30],
        # Backwards-compatible flat metrics.
        "total_users": overview["totalUsers"],
        "daily_active_users": overview["activeUsers7d"],
        "workouts_last_7_days": overview["workoutsLogged7d"],
        "daily_logs_last_7_days": overview["dailyLogs7d"],
    }
