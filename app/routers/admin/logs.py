from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.routers.admin.auth import verify_admin   # <-- ADD THIS

router = APIRouter(prefix="/admin/logs", tags=["Admin Logs"])


@router.get("")
def get_all_logs(
    db: Session = Depends(get_db),
    admin=Depends(verify_admin)   # <-- PROTECT ROUTE
):
    logs = {}

    # Workout Logs
    try:
        from app.models.workout_log import WorkoutLog
        logs["workout_logs"] = (
            db.query(WorkoutLog)
            .order_by(WorkoutLog.date.desc())
            .all()
        )
    except:
        logs["workout_logs"] = []

    # Sports Logs
    try:
        from app.models.sports_log import SportsLog
        logs["sports_logs"] = (
            db.query(SportsLog)
            .order_by(SportsLog.date.desc())
            .all()
        )
    except:
        logs["sports_logs"] = []

    # Free Training Logs
    try:
        from app.models.free_training_log import FreeTrainingLog
        logs["free_training_logs"] = (
            db.query(FreeTrainingLog)
            .order_by(FreeTrainingLog.date.desc())
            .all()
        )
    except:
        logs["free_training_logs"] = []

    # Daily Logs
    try:
        from app.models.daily_log import DailyLog
        logs["daily_logs"] = (
            db.query(DailyLog)
            .order_by(DailyLog.date.desc())
            .all()
        )
    except:
        logs["daily_logs"] = []

    # Login Logs
    try:
        from app.models.login_log import LoginLog
        logs["login_logs"] = (
            db.query(LoginLog)
            .order_by(LoginLog.timestamp.desc())
            .all()
        )
    except:
        logs["login_logs"] = []

    return logs
