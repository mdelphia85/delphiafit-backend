from sqlalchemy.orm import Session
from app.models.daily_log import DailyLog
from app.schemas.daily_log import DailyLogCreate

# -----------------------------
# CREATE DAILY LOG
# -----------------------------
def create_daily_log(db: Session, data: DailyLogCreate) -> DailyLog:
    log = DailyLog(
        user_id=data.user_id,
        date=data.date,
        mood=data.mood,
        energy_level=data.energy_level,
        notes=data.notes,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

# -----------------------------
# GET DAILY LOGS FOR USER
# -----------------------------
def get_daily_logs(db: Session, user_id: int):
    return (
        db.query(DailyLog)
        .filter(DailyLog.user_id == user_id)
        .order_by(DailyLog.date.desc())
        .all()
    )
