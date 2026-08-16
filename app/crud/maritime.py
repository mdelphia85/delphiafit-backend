from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.maritime import MaritimeLog


def create_maritime_log(db: Session, data: dict) -> MaritimeLog:
    log = MaritimeLog(**data)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_maritime_log(db: Session, log_id: int) -> Optional[MaritimeLog]:
    return db.query(MaritimeLog).filter(MaritimeLog.id == log_id).first()


def get_maritime_logs(db: Session) -> List[MaritimeLog]:
    return db.query(MaritimeLog).all()


def update_maritime_log(db: Session, log_id: int, data: dict) -> Optional[MaritimeLog]:
    log = get_maritime_log(db, log_id)
    if not log:
        return None

    for field, value in data.items():
        setattr(log, field, value)

    db.commit()
    db.refresh(log)
    return log


def delete_maritime_log(db: Session, log_id: int) -> bool:
    log = get_maritime_log(db, log_id)
    if not log:
        return False

    db.delete(log)
    db.commit()
    return True
