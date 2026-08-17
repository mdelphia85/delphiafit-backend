from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.sports_log import SportsLog
from app.schemas.sports_log import SportsLogCreate, SportsLogUpdate


def create_sports_log(db: Session, user_id: int, data: SportsLogCreate) -> SportsLog:
    log = SportsLog(
        user_id=user_id,
        metric_name=data.metric_name,
        value=data.value,
        date=data.date,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_sports_log(db: Session, log_id: int) -> Optional[SportsLog]:
    return db.query(SportsLog).filter(SportsLog.id == log_id).first()


def get_sports_logs(db: Session, user_id: int) -> List[SportsLog]:
    return (
        db.query(SportsLog)
        .filter(SportsLog.user_id == user_id)
        .order_by(SportsLog.date.desc())
        .all()
    )


def update_sports_log(db: Session, log_id: int, data: SportsLogUpdate) -> Optional[SportsLog]:
    log = get_sports_log(db, log_id)
    if not log:
        return None

    for field, value in data.dict(exclude_unset=True).items():
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
