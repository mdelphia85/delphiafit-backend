from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.weight import WeightLog
from app.schemas.weight import WeightCreate, WeightUpdate


def create_weight_log(db: Session, data: WeightCreate) -> WeightLog:
    log = WeightLog(
        user_id=data.user_id,
        weight=data.weight,
        unit=data.unit,
        logged_at=data.logged_at or datetime.utcnow(),
        notes=data.notes,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_weight_log(db: Session, log_id: int) -> Optional[WeightLog]:
    return db.query(WeightLog).filter(WeightLog.id == log_id).first()


def get_weight_logs_for_user(db: Session, user_id: int) -> List[WeightLog]:
    return (
        db.query(WeightLog)
        .filter(WeightLog.user_id == user_id)
        .order_by(WeightLog.logged_at.desc())
        .all()
    )


def update_weight_log(db: Session, log_id: int, data: WeightUpdate) -> Optional[WeightLog]:
    log = get_weight_log(db, log_id)
    if not log:
        return None

    for field, value in data.dict(exclude_unset=True).items():
        setattr(log, field, value)

    db.commit()
    db.refresh(log)
    return log


def delete_weight_log(db: Session, log_id: int) -> bool:
    log = get_weight_log(db, log_id)
    if not log:
        return False

    db.delete(log)
    db.commit()
    return True
