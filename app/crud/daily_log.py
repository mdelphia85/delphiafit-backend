from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.daily_log import DailyLog
from app.schemas.daily_log import DailyLogCreate, DailyLogUpdate


def create_daily_log(db: Session, data: DailyLogCreate) -> DailyLog:
    log = DailyLog(
        user_id=data.user_id,
        mood=data.mood,
        energy=data.energy,
        notes=data.notes,
        timestamp=data.timestamp or datetime.utcnow(),
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_daily_log(db: Session, log_id: int) -> Optional[DailyLog]:
    return db.query(DailyLog).filter(DailyLog.id == log_id).first()


def get_daily_logs_for_user(db: Session, user_id: int) -> List[DailyLog]:
    return (
        db.query(DailyLog)
        .filter(DailyLog.user_id == user_id)
        .order_by(DailyLog.timestamp.desc())
        .all()
    )


def update_daily_log(db: Session, log_id: int, data: DailyLogUpdate) -> Optional[DailyLog]:
    log = get_daily_log(db, log_id)
    if not log:
        return None

    for field, value in data.dict(exclude_unset=True).items():
        setattr(log, field, value)

    db.commit()
    db.refresh(log)
    return log


def delete_daily_log(db: Session, log_id: int) -> bool:
    log = get_daily_log(db, log_id)
    if not log:
        return False

    db.delete(log)
    db.commit()
    return True
