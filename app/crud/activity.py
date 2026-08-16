from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.activity import Activity
from app.schemas.activity import ActivityCreate, ActivityUpdate


def create_activity(db: Session, data: ActivityCreate) -> Activity:
    activity = Activity(
        user_id=data.user_id,
        activity_type=data.activity_type,
        duration=data.duration,
        intensity=data.intensity,
        notes=data.notes,
        timestamp=data.timestamp or datetime.utcnow(),
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


def get_activity(db: Session, activity_id: int) -> Optional[Activity]:
    return db.query(Activity).filter(Activity.id == activity_id).first()


def get_activities_for_user(db: Session, user_id: int) -> List[Activity]:
    return (
        db.query(Activity)
        .filter(Activity.user_id == user_id)
        .order_by(Activity.timestamp.desc())
        .all()
    )


def update_activity(db: Session, activity_id: int, data: ActivityUpdate) -> Optional[Activity]:
    activity = get_activity(db, activity_id)
    if not activity:
        return None

    for field, value in data.dict(exclude_unset=True).items():
        setattr(activity, field, value)

    db.commit()
    db.refresh(activity)
    return activity


def delete_activity(db: Session, activity_id: int) -> bool:
    activity = get_activity(db, activity_id)
    if not activity:
        return False

    db.delete(activity)
    db.commit()
    return True
