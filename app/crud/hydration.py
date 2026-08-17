from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.hydration import HydrationLog
from app.schemas.hydration import HydrationLogCreate, HydrationLogUpdate


def create_hydration_log(db: Session, user_id: int, data: HydrationLogCreate) -> HydrationLog:
    log = HydrationLog(
        user_id=user_id,
        amount_ml=data.amount_ml,
        date=data.date,
        notes=data.notes,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_hydration_log(db: Session, log_id: int) -> Optional[HydrationLog]:
    return db.query(HydrationLog).filter(HydrationLog.id == log_id).first()


def get_hydration_logs(db: Session, user_id: int) -> List[HydrationLog]:
    return (
        db.query(HydrationLog)
        .filter(HydrationLog.user_id == user_id)
        .order_by(HydrationLog.date.desc())
        .all()
    )


def update_hydration_log(db: Session, log_id: int, data: HydrationLogUpdate) -> Optional[HydrationLog]:
    log = get_hydration_log(db, log_id)
    if not log:
        return None

    for field, value in data.dict(exclude_unset=True).items():
        setattr(log, field, value)

    db.commit()
    db.refresh(log)
    return log


def delete_hydration_log(db: Session, log_id: int) -> bool:
    log = get_hydration_log(db, log_id)
    if not log:
        return False

    db.delete(log)
    db.commit()
    return True
