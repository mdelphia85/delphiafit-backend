from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.daily_log import DailyLog
from app.schemas.daily_log import DailyLogCreate, DailyLogUpdate


def create_daily_log(db: Session, user_id: int, data: DailyLogCreate) -> DailyLog:
    values = data.model_dump(exclude_none=True)
    log = DailyLog(user_id=user_id, **values)
    db.add(log); db.commit(); db.refresh(log); return log


def get_daily_log(db: Session, log_id: int) -> Optional[DailyLog]:
    return db.query(DailyLog).filter(DailyLog.id == log_id).first()


def get_daily_logs(db: Session, user_id: int) -> List[DailyLog]:
    return db.query(DailyLog).filter(DailyLog.user_id == user_id).order_by(DailyLog.date.desc()).all()


def update_daily_log(db: Session, log_id: int, data: DailyLogUpdate) -> Optional[DailyLog]:
    log=get_daily_log(db,log_id)
    if not log:return None
    for field,value in data.model_dump(exclude_unset=True).items(): setattr(log,field,value)
    db.commit();db.refresh(log);return log


def delete_daily_log(db: Session, log_id: int) -> bool:
    log=get_daily_log(db,log_id)
    if not log:return False
    db.delete(log);db.commit();return True
