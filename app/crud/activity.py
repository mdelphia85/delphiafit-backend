from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.activity import ActivityLog
from app.schemas.activity import ActivityLogCreate, ActivityLogUpdate


def create_activity_log(db: Session, data: ActivityLogCreate) -> ActivityLog:
    activity = ActivityLog(
        user_id=data.user_id,
        activity_type=data.activity_type,
        duration_minutes=data.duration_minutes,
        calories_burned=data.calories_burned,
        notes=data.notes,
        date=data.date or datetime.utcnow(),
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


def get_activity_log(db: Session, activity_id: int) -> Optional[ActivityLog]:
    return db.query(ActivityLog).filter(ActivityLog.id == activity_id).first()


def get_activity_logs(db: Session, user_id: int) -> List[ActivityLog]:
    return (
        db.query(ActivityLog)
        .filter(ActivityLog.user_id == user_id)
        .order_by(ActivityLog.date.desc())
        .all()
    )


def update_activity_log(db: Session, activity_id: int, data: ActivityLogUpdate) -> Optional[ActivityLog]:
    activity = get_activity_log(db, activity_id)
    if not activity:
        return None

    for field, value in data.dict(exclude_unset=True).items():
        setattr(activity, field, value)

    db.commit()
    db.refresh(activity)
    return activity


def delete_activity_log(db: Session, activity_id: int) -> bool:
    activity = get_activity_log(db, activity_id)
    if not activity:
        return False

    db.delete(activity)
    db.commit()
    return True
