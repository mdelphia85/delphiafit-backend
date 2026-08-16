from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.recovery import RecoveryLog
from app.schemas.recovery import RecoveryCreate, RecoveryUpdate


def create_recovery_log(db: Session, data: RecoveryCreate) -> RecoveryLog:
    log = RecoveryLog(
        user_id=data.user_id,
        recovery_type=data.recovery_type,
        duration=data.duration,
        notes=data.notes,
        timestamp=data.timestamp or datetime.utcnow(),
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_recovery_log(db: Session, log_id: int) -> Optional[RecoveryLog]:
    return db.query(RecoveryLog).filter(RecoveryLog.id == log_id).first()


def get_recovery_logs_for_user(db: Session, user_id: int) -> List[RecoveryLog]:
    return (
        db.query(RecoveryLog)
        .filter(RecoveryLog.user_id == user_id)
        .order_by(RecoveryLog.timestamp.desc())
        .all()
    )


def update_recovery_log(db: Session, log_id: int, data: RecoveryUpdate) -> Optional[RecoveryLog]:
    log = get_recovery_log(db, log_id)
    if not log:
        return None

    for field, value in data.dict(exclude_unset=True).items():
        setattr(log, field, value)

    db.commit()
    db.refresh(log)
    return log


def delete_recovery_log(db: Session, log_id: int) -> bool:
    log = get_recovery_log(db, log_id)
    if not log:
        return False

    db.delete(log)
    db.commit()
    return True
