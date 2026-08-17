from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.rep_logs import RepLog
from app.schemas.rep_logs import RepLogCreate, RepLogUpdate


def create_rep_log(db: Session, user_id: int, data: RepLogCreate) -> RepLog:
    log = RepLog(
        user_id=user_id,
        exercise=data.exercise,
        reps=data.reps,
        weight=data.weight,
        timestamp=data.timestamp or datetime.utcnow(),
        notes=data.notes,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_rep_log(db: Session, log_id: int) -> Optional[RepLog]:
    return db.query(RepLog).filter(RepLog.id == log_id).first()


def get_rep_logs(db: Session, user_id: int) -> List[RepLog]:
    return (
        db.query(RepLog)
        .filter(RepLog.user_id == user_id)
        .order_by(RepLog.timestamp.desc())
        .all()
    )


def update_rep_log(db: Session, log_id: int, data: RepLogUpdate) -> Optional[RepLog]:
    log = get_rep_log(db, log_id)
    if not log:
        return None

    for field, value in data.dict(exclude_unset=True).items():
        setattr(log, field, value)

    db.commit()
    db.refresh(log)
    return log


def delete_rep_log(db: Session, log_id: int) -> bool:
    log = get_rep_log(db, log_id)
    if not log:
        return False

    db.delete(log)
    db.commit()
    return True
