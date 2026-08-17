from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.weight import WeightLog
from app.schemas.weight import WeightLogCreate, WeightLogUpdate


def create_weight_log(db: Session, user_id: int, data: WeightLogCreate) -> WeightLog:
    log = WeightLog(
        user_id=user_id,
        weight_kg=data.weight_kg,
        body_fat_percent=data.body_fat_percent,
        date=data.date,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_weight_log(db: Session, log_id: int) -> Optional[WeightLog]:
    return db.query(WeightLog).filter(WeightLog.id == log_id).first()


def get_weight_logs(db: Session, user_id: int) -> List[WeightLog]:
    return (
        db.query(WeightLog)
        .filter(WeightLog.user_id == user_id)
        .order_by(WeightLog.date.desc())
        .all()
    )


def update_weight_log(db: Session, log_id: int, data: WeightLogUpdate) -> Optional[WeightLog]:
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
