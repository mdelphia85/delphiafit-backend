from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.body_metrics import BodyMetrics
from app.schemas.body_metrics import BodyMetricsCreate, BodyMetricsUpdate


def create_body_metrics(db: Session, data: BodyMetricsCreate) -> BodyMetrics:
    metrics = BodyMetrics(
        user_id=data.user_id,
        height_cm=data.height_cm,
        weight_kg=data.weight_kg,
        body_fat_percent=data.body_fat_percent,
        muscle_mass_kg=data.muscle_mass_kg,
        waist_cm=data.waist_cm,
        hips_cm=data.hips_cm,
        chest_cm=data.chest_cm,
        date=data.date,
    )
    db.add(metrics)
    db.commit()
    db.refresh(metrics)
    return metrics


def get_body_metrics(db: Session, metrics_id: int) -> Optional[BodyMetrics]:
    return db.query(BodyMetrics).filter(BodyMetrics.id == metrics_id).first()


def get_body_metrics_for_user(db: Session, user_id: int) -> List[BodyMetrics]:
    return (
        db.query(BodyMetrics)
        .filter(BodyMetrics.user_id == user_id)
        .order_by(BodyMetrics.date.desc())
        .all()
    )


def update_body_metrics(db: Session, metrics_id: int, data: BodyMetricsUpdate) -> Optional[BodyMetrics]:
    metrics = get_body_metrics(db, metrics_id)
    if not metrics:
        return None

    for field, value in data.dict(exclude_unset=True).items():
        setattr(metrics, field, value)

    db.commit()
    db.refresh(metrics)
    return metrics


def delete_body_metrics(db: Session, metrics_id: int) -> bool:
    metrics = get_body_metrics(db, metrics_id)
    if not metrics:
        return False

    db.delete(metrics)
    db.commit()
    return True
