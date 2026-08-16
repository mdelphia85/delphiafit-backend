from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.aviation import AviationLog


def create_aviation_log(db: Session, data: dict) -> AviationLog:
    log = AviationLog(**data)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_aviation_log(db: Session, log_id: int) -> Optional[AviationLog]:
    return db.query(AviationLog).filter(AviationLog.id == log_id).first()


def get_aviation_logs(db: Session) -> List[AviationLog]:
    return db.query(AviationLog).all()


def update_aviation_log(db: Session, log_id: int, data: dict) -> Optional<AviationLog]:
    log = get_aviation_log(db, log_id)
    if not log:
        return None

    for field, value in data.items():
        setattr(log, field, value)

    db.commit()
    db.refresh(log)
    return log


def delete_aviation_log(db: Session, log_id: int) -> bool:
    log = get_aviation_log(db, log_id)
    if not log:
        return False

    db.delete(log)
    db.commit()
    return True
