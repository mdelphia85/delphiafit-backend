from sqlalchemy.orm import Session
from app.models.nutrition import NutritionLog
from app.schemas.nutrition import NutritionLogCreate

def create_nutrition_log(db: Session, user_id: int, data: NutritionLogCreate):
    log = NutritionLog(
        user_id=user_id,
        calories=data.calories,
        protein=data.protein,
        carbs=data.carbs,
        fats=data.fats,
        water_oz=data.water_oz,
        notes=data.notes
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

def get_nutrition_logs(db: Session, user_id: int):
    return db.query(NutritionLog).filter(NutritionLog.user_id == user_id).all()
