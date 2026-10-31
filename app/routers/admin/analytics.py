from collections import Counter
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.daily_log import DailyLog
from app.models.login_log import LoginLog
from app.models.sports_log import SportsLog
from app.models.user import User
from app.models.workout_log import WorkoutLog
from app.routers.admin.auth import verify_admin

router = APIRouter(prefix="/admin/analytics", tags=["Admin Analytics"])


def _day(value) -> str | None:
    return value.date().isoformat() if value else None


@router.get("")
def get_admin_analytics(db: Session = Depends(get_db), admin=Depends(verify_admin)):
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)

    workouts = db.query(WorkoutLog).filter(WorkoutLog.date >= week_ago).all()
    daily_logs = db.query(DailyLog).filter(DailyLog.date >= week_ago).all()
    sports = db.query(SportsLog).filter(SportsLog.date >= week_ago).all()
    logins = db.query(LoginLog).filter(LoginLog.timestamp >= week_ago).all()
    new_users = db.query(User).filter(User.created_at >= week_ago).all()

    active_ids = {
        row.user_id for rows in (workouts, daily_logs, sports, logins) for row in rows
    }

    names = Counter(
        [(row.workout_type or row.manual_name or row.mode or "Workout") for row in workouts]
        + [row.sport for row in sports if row.sport]
    )
    top_workouts = [{"label": label, "count": count} for label, count in names.most_common(8)]

    # Resolve emails only for users that appear in the recent rows.
    recent_workouts = sorted(workouts, key=lambda r: r.date or now, reverse=True)[:30]
    recent_daily = sorted(daily_logs, key=lambda r: r.date or now, reverse=True)[:30]
    recent_sports = sorted(sports, key=lambda r: r.date or now, reverse=True)[:30]
    needed = {r.user_id for r in recent_workouts + recent_daily + recent_sports}
    email_by_id = (
        {u.id: u.email for u in db.query(User).filter(User.id.in_(needed)).all()} if needed else {}
    )

    activity = []
    for row in recent_workouts:
        activity.append({
            "id": f"workout-{row.id}", "type": "workout",
            "detail": row.workout_type or row.manual_name or "Workout logged",
            "user": email_by_id.get(row.user_id, "Unknown user"),
            "time": row.date.isoformat() if row.date else None,
        })
    for row in recent_daily:
        activity.append({
            "id": f"daily-{row.id}", "type": "daily", "detail": "Daily log saved",
            "user": email_by_id.get(row.user_id, "Unknown user"),
            "time": row.date.isoformat() if row.date else None,
        })
    for row in recent_sports:
        activity.append({
            "id": f"sports-{row.id}", "type": "sports", "detail": f"Sports session: {row.sport}",
            "user": email_by_id.get(row.user_id, "Unknown user"),
            "time": row.date.isoformat() if row.date else None,
        })
    activity.sort(key=lambda item: item.get("time") or "", reverse=True)

    days = [(now - timedelta(days=offset)).date().isoformat() for offset in range(6, -1, -1)]
    series = {d: {"date": d, "logins": 0, "workouts": 0, "dailyLogs": 0, "signups": 0} for d in days}
    for rows, key, attr in (
        (logins, "logins", "timestamp"),
        (workouts, "workouts", "date"),
        (daily_logs, "dailyLogs", "date"),
        (new_users, "signups", "created_at"),
    ):
        for row in rows:
            bucket = series.get(_day(getattr(row, attr)))
            if bucket:
                bucket[key] += 1

    overview = {
        "totalUsers": db.query(User).count(),
        "activeUsers7d": len(active_ids),
        "newUsers7d": len(new_users),
        "logins7d": len(logins),
        "workoutsLogged7d": len(workouts),
        "dailyLogs7d": len(daily_logs),
        "sportsLogs7d": len(sports),
    }
    return {
        "overview": overview,
        "top_workouts": top_workouts,
        "recent_activity": activity[:30],
        "daily_series": list(series.values()),
        # Backwards-compatible flat metrics.
        "total_users": overview["totalUsers"],
        "daily_active_users": overview["activeUsers7d"],
        "workouts_last_7_days": overview["workoutsLogged7d"],
        "daily_logs_last_7_days": overview["dailyLogs7d"],
    }
