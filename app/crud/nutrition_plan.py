from sqlalchemy.orm import Session
from app.models.macros import MacroPlan
from app.schemas.macros import MacroPlanCreate

def create_nutrition_plan(db: Session, user_id: int, data: MacroPlanCreate):
    plan = MacroPlan(
        user_id=user_id,
        daily_calories=data.daily_calories,
        daily_protein=data.daily_protein,
        daily_carbs=data.daily_carbs,
        daily_fats=data.daily_fats
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan

def get_nutrition_plans(db: Session, user_id: int):
    return db.query(MacroPlan).filter(MacroPlan.user_id == user_id).all()
