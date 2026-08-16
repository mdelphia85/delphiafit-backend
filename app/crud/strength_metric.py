from sqlalchemy.orm import Session
from app.models.strength_metric import StrengthMetric
from app.schemas.strength_metric import StrengthMetricCreate

def create_strength_metric(db: Session, user_id: int, data: StrengthMetricCreate):
    metric = StrengthMetric(
        user_id=user_id,
        metric_name=data.metric_name,
        value=data.value
    )
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return metric

def get_strength_metrics(db: Session, user_id: int):
    return db.query(StrengthMetric).filter(StrengthMetric.user_id == user_id).all()
