from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.nutrition import NutritionLog
from app.schemas.nutrition import NutritionLogCreate, NutritionLogUpdate


def create_nutrition_log(db: Session, user_id: int, data: NutritionLogCreate) -> NutritionLog:
    log = NutritionLog(
        user_id=user_id,
        calories=data.calories,
        protein=data.protein,
        carbs=data.carbs,
        fats=data.fats,
        water_oz=data.water_oz,
        notes=data.notes,
        recorded_at=datetime.utcnow(),
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_nutrition_log(db: Session, log_id: int) -> Optional[NutritionLog]:
    return db.query(NutritionLog).filter(NutritionLog.id == log_id).first()


def get_nutrition_logs(db: Session, user_id: int) -> List[NutritionLog]:
    return (
        db.query(NutritionLog)
        .filter(NutritionLog.user_id == user_id)
        .order_by(NutritionLog.recorded_at.desc())
        .all()
    )


def update_nutrition_log(db: Session, log_id: int, data: NutritionLogUpdate) -> Optional[NutritionLog]:
    log = get_nutrition_log(db, log_id)
    if not log:
        return None

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(log, field, value)

    db.commit()
    db.refresh(log)
    return log


def delete_nutrition_log(db: Session, log_id: int) -> bool:
    log = get_nutrition_log(db, log_id)
    if not log:
        return False

    db.delete(log)
    db.commit()
    return True
