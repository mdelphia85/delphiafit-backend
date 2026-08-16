from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.free_training_log import FreeTrainingLog


def create_free_training_log(db: Session, data: dict) -> FreeTrainingLog:
    log = FreeTrainingLog(**data)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_free_training_log(db: Session, log_id: int) -> Optional[FreeTrainingLog]:
    return db.query(FreeTrainingLog).filter(FreeTrainingLog.id == log_id).first()


def get_free_training_logs_for_user(db: Session, user_id: int) -> List[FreeTrainingLog]:
    return db.query(FreeTrainingLog).filter(FreeTrainingLog.user_id == user_id).all()


def update_free_training_log(db: Session, log_id: int, data: dict) -> Optional[FreeTrainingLog]:
    log = get_free_training_log(db, log_id)
    if not log:
        return None

    for field, value in data.items():
        setattr(log, field, value)

    db.commit()
    db.refresh(log)
    return log


def delete_free_training_log(db: Session, log_id: int) -> bool:
    log = get_free_training_log(db, log_id)
    if not log:
        return False

    db.delete(log)
    db.commit()
    return True
