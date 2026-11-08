from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.sleep import SleepLog
from app.schemas.sleep import SleepLogCreate, SleepLogUpdate


def create_sleep_log(db: Session, user_id: int, data: SleepLogCreate) -> SleepLog:
    log = SleepLog(
        user_id=user_id,
        duration_hours=data.duration_hours,
        quality=data.quality,
        notes=data.notes,
        date=data.date,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_sleep_log(db: Session, log_id: int) -> Optional[SleepLog]:
    return db.query(SleepLog).filter(SleepLog.id == log_id).first()


def get_sleep_logs(db: Session, user_id: int) -> List[SleepLog]:
    return (
        db.query(SleepLog)
        .filter(SleepLog.user_id == user_id)
        .order_by(SleepLog.date.desc())
        .all()
    )


def update_sleep_log(db: Session, log_id: int, data: SleepLogUpdate) -> Optional[SleepLog]:
    log = get_sleep_log(db, log_id)
    if not log:
        return None

    for field, value in data.model_dump(exclude_unset=True).items():
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
