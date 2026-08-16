from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.sports_log import SportsLog


def create_sports_log(db: Session, data: dict) -> SportsLog:
    log = SportsLog(**data)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_sports_log(db: Session, log_id: int) -> Optional[SportsLog]:
    return db.query(SportsLog).filter(SportsLog.id == log_id).first()


def get_sports_logs_for_user(db: Session, user_id: int) -> List[SportsLog]:
    return db.query(SportsLog).filter(SportsLog.user_id == user_id).all()


def update_sports_log(db: Session, log_id: int, data: dict) -> Optional[SportsLog]:
    log = get_sports_log(db, log_id)
    if not log:
        return None

    for field, value in data.items():
        setattr(log, field, value)

    db.commit()
    db.refresh(log)
    return log


def delete_sports_log(db: Session, log_id: int) -> bool:
    log = get_sports_log(db, log_id)
    if not log:
        return False

    db.delete(log)
    db.commit()
    return True
