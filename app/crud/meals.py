from sqlalchemy.orm import Session
from app.models.meals import Meal
from app.schemas.meals import MealCreate

def create_meal(db: Session, user_id: int, data: MealCreate):
    meal = Meal(
        user_id=user_id,
        name=data.name,
        calories=data.calories,
        protein=data.protein,
        carbs=data.carbs,
        fats=data.fats
    )
    db.add(meal)
    db.commit()
    db.refresh(meal)
    return meal

def get_meals(db: Session, user_id: int):
    return db.query(Meal).filter(Meal.user_id == user_id).all()
