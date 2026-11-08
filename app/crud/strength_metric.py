from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.strength_metric import StrengthMetric
from app.schemas.strength_metric import StrengthMetricCreate, StrengthMetricUpdate


def create_strength_metric(db: Session, user_id: int, data: StrengthMetricCreate) -> StrengthMetric:
    metric = StrengthMetric(
        user_id=user_id,
        metric_name=data.metric_name,
        value=data.value,
    )
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return metric


def get_strength_metric(db: Session, metric_id: int) -> Optional[StrengthMetric]:
    return db.query(StrengthMetric).filter(StrengthMetric.id == metric_id).first()


def get_strength_metrics(db: Session, user_id: int) -> List[StrengthMetric]:
    return (
        db.query(StrengthMetric)
        .filter(StrengthMetric.user_id == user_id)
        .order_by(StrengthMetric.created_at.desc())
        .all()
    )


def update_strength_metric(db: Session, metric_id: int, data: StrengthMetricUpdate) -> Optional[StrengthMetric]:
    metric = get_strength_metric(db, metric_id)
    if not metric:
        return None

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(metric, field, value)

    db.commit()
    db.refresh(metric)
    return metric


def delete_strength_metric(db: Session, metric_id: int) -> bool:
    metric = get_strength_metric(db, metric_id)
    if not metric:
        return False

    db.delete(metric)
    db.commit()
    return True
