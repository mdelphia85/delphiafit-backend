from sqlalchemy.orm import Session
from app.models.rep_logs import RepLog
from app.schemas.rep_logs import RepLogCreate

def create_rep_log(db: Session, user_id: int, data: RepLogCreate):
    log = RepLog(
        user_id=user_id,
        exercise_name=data.exercise_name,
        reps=data.reps,
        weight=data.weight
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

def get_rep_logs(db: Session, user_id: int):
    return db.query(RepLog).filter(RepLog.user_id == user_id).all()
