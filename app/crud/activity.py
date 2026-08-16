from sqlalchemy.orm import Session
from app.models.activity import ActivityLog
from app.schemas.activity import ActivityLogCreate

def create_activity_log(db: Session, data: ActivityLogCreate) -> ActivityLog:
    log = ActivityLog(
        user_id=data.user_id,
        activity_type=data.activity_type,
        duration_minutes=data.duration_minutes,
        calories_burned=data.calories_burned,
        notes=data.notes,
        date=data.date,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

def get_activity_logs(db: Session, user_id: int):
    return (
        db.query(ActivityLog)
        .filter(ActivityLog.user_id == user_id)
        .order_by(ActivityLog.date.desc())
        .all()
    )
