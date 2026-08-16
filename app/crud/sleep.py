from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.sleep import SleepLog
from app.schemas.sleep import SleepCreate, SleepUpdate


def create_sleep_log(db: Session, data: SleepCreate) -> SleepLog:
    log = SleepLog(
        user_id=data.user_id,
        duration=data.duration,
        quality=data.quality,
        notes=data.notes,
        timestamp=data.timestamp or datetime.utcnow(),
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_sleep_log(db: Session, log_id: int) -> Optional[SleepLog]:
    return db.query(SleepLog).filter(SleepLog.id == log_id).first()


def get_sleep_logs_for_user(db: Session, user_id: int) -> List[SleepLog]:
    return (
        db.query(SleepLog)
        .filter(SleepLog.user_id == user_id)
        .order_by(SleepLog.timestamp.desc())
        .all()
    )


def update_sleep_log(db: Session, log_id: int, data: SleepUpdate) -> Optional[SleepLog]:
    log = get_sleep_log(db, log_id)
    if not log:
        return None

    for field, value in data.dict(exclude_unset=True).items():
        setattr(log, field, value)

    db.commit()
    db.refresh(log)
    return log


def delete_sleep_log(db: Session, log_id: int) -> bool:
    log = get_sleep_log(db, log_id)
    if not log:
        return False

    db.delete(log)
    db.commit()
    return True
