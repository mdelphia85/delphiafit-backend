from sqlalchemy.orm import Session
from app.models.weight import WeightLog
from app.schemas.weight import WeightLogCreate

def create_weight_log(db: Session, data: WeightLogCreate) -> WeightLog:
    weight_log = WeightLog(
        user_id=data.user_id,
        weight=data.weight,
        body_fat=data.body_fat,
        date=data.date
    )
    db.add(weight_log)
    db.commit()
    db.refresh(weight_log)
    return weight_log

def get_weight_logs(db: Session, user_id: int):
    return db.query(WeightLog).filter(WeightLog.user_id == user_id).all()
