from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.nutrition import NutritionLog
from app.schemas.nutrition import NutritionCreate, NutritionUpdate


def create_nutrition_log(db: Session, data: NutritionCreate) -> NutritionLog:
    log = NutritionLog(
        user_id=data.user_id,
        calories=data.calories,
        protein=data.protein,
        carbs=data.carbs,
        fats=data.fats,
        timestamp=data.timestamp or datetime.utcnow(),
        notes=data.notes,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_nutrition_log(db: Session, log_id: int) -> Optional[NutritionLog]:
    return db.query(NutritionLog).filter(NutritionLog.id == log_id).first()


def get_nutrition_logs_for_user(db: Session, user_id: int) -> List[NutritionLog]:
    return (
        db.query(NutritionLog)
        .filter(NutritionLog.user_id == user_id)
        .order_by(NutritionLog.timestamp.desc())
        .all()
    )


def update_nutrition_log(db: Session, log_id: int, data: NutritionUpdate) -> Optional[NutritionLog]:
    log = get_nutrition_log(db, log_id)
    if not log:
        return None

    for field, value in data.dict(exclude_unset=True).items():
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
