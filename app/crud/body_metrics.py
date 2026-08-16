from sqlalchemy.orm import Session
from app.models.body_metrics import BodyMetric
from app.schemas.body_metrics import BodyMetricCreate

def create_body_metric(db: Session, data: BodyMetricCreate) -> BodyMetric:
    metric = BodyMetric(
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
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return metric

def get_body_metrics(db: Session, user_id: int):
    return (
        db.query(BodyMetric)
        .filter(BodyMetric.user_id == user_id)
        .order_by(BodyMetric.date.desc())
        .all()
    )
