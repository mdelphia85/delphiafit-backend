from sqlalchemy.orm import Session
from app.models.hydration import HydrationLog
from app.schemas.hydration import HydrationLogCreate

def create_hydration_log(db: Session, data: HydrationLogCreate) -> HydrationLog:
    log = HydrationLog(
        user_id=data.user_id,
        amount_ml=data.amount_ml,
        date=data.date,
        notes=data.notes,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

def get_hydration_logs(db: Session, user_id: int):
    return (
        db.query(HydrationLog)
        .filter(HydrationLog.user_id == user_id)
        .order_by(HydrationLog.date.desc())
        .all()
    )
