from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.workout_log import WorkoutLog
from app.schemas.workout_log import WorkoutLogCreate, WorkoutLogUpdate


def create_workout_log(db: Session, data: WorkoutLogCreate) -> WorkoutLog:
    log = WorkoutLog(
        user_id=data.user_id,
        workout_type=data.workout_type,
        duration=data.duration,
        intensity=data.intensity,
        notes=data.notes,
        timestamp=data.timestamp or datetime.utcnow(),
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_workout_log(db: Session, log_id: int) -> Optional[WorkoutLog]:
    return db.query(WorkoutLog).filter(WorkoutLog.id == log_id).first()


def get_workout_logs_for_user(db: Session, user_id: int) -> List[WorkoutLog]:
    return (
        db.query(WorkoutLog)
        .filter(WorkoutLog.user_id == user_id)
        .order_by(WorkoutLog.timestamp.desc())
        .all()
    )


def update_workout_log(db: Session, log_id: int, data: WorkoutLogUpdate) -> Optional[WorkoutLog]:
    log = get_workout_log(db, log_id)
    if not log:
        return None

    for field, value in data.dict(exclude_unset=True).items():
        setattr(log, field, value)

    db.commit()
    db.refresh(log)
    return log


def delete_workout_log(db: Session, log_id: int) -> bool:
    log = get_workout_log(db, log_id)
    if not log:
        return False

    db.delete(log)
    db.commit()
    return True
