from sqlalchemy.orm import Session
from app.models.sleep import SleepLog
from app.schemas.sleep import SleepLogCreate

def create_sleep_log(db: Session, data: SleepLogCreate) -> SleepLog:
    log = SleepLog(
        user_id=data.user_id,
        duration_hours=data.duration_hours,
        quality=data.quality,
        notes=data.notes,
        date=data.date,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

def get_sleep_logs(db: Session, user_id: int):
    return (
        db.query(SleepLog)
        .filter(SleepLog.user_id == user_id)
        .order_by(SleepLog.date.desc())
        .all()
    )
