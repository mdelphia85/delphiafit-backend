from sqlalchemy.orm import Session
from app.models.recovery import RecoveryLog
from app.schemas.recovery import RecoveryCreate

def create_recovery_log(db: Session, user_id: int, data: RecoveryCreate):
    log = RecoveryLog(
        user_id=user_id,
        sleep_hours=data.sleep_hours,
        soreness_level=data.soreness_level,
        readiness_score=data.readiness_score,
        notes=data.notes
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

def get_recovery_logs(db: Session, user_id: int):
    return db.query(RecoveryLog).filter(RecoveryLog.user_id == user_id).all()
