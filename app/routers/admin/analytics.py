from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.database.connection import get_db
from app.models.user import User

# If you have these models, import them:
# from app.models.daily_log import DailyLog
# from app.models.workout_log import WorkoutLog
# from app.models.sports_log import SportsLog

router = APIRouter(prefix="/admin/analytics", tags=["Admin Analytics"])


@router.get("/")
def get_admin_analytics(
    db: Session = Depends(get_db)
):
    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=7)

    # -----------------------------
    # TOTAL USERS
    # -----------------------------
    total_users = db.query(User).count()

    # -----------------------------
    # NEW USERS (LAST 7 DAYS)
    # -----------------------------
    new_users = (
        db.query(User)
        .filter(User.created_at >= week_ago)
        .count()
    )

    # -----------------------------
    # DAILY ACTIVE USERS (DAU)
    # -----------------------------
    try:
        from app.models.daily_log import DailyLog
        dau = (
            db.query(DailyLog.user_id)
            .filter(DailyLog.date == today)
            .distinct()
            .count()
        )
    except:
        dau = 0

    # -----------------------------
    # WORKOUT COUNT (LAST 7 DAYS)
    # -----------------------------
    try:
        from app.models.workout_log import WorkoutLog
        workouts_last_week = (
            db.query(WorkoutLog)
            .filter(WorkoutLog.date >= week_ago)
            .count()
        )
    except:
        workouts_last_week = 0

    # -----------------------------
    # SPORTS SESSIONS (LAST 7 DAYS)
    # -----------------------------
    try:
        from app.models.sports_log import SportsLog
        sports_last_week = (
            db.query(SportsLog)
            .filter(SportsLog.date >= week_ago)
            .count()
        )
    except:
        sports_last_week = 0

    return {
        "total_users": total_users,
        "new_users_last_7_days": new_users,
        "daily_active_users": dau,
        "workouts_last_7_days": workouts_last_week,
        "sports_last_7_days": sports_last_week,
    }
