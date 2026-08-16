from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.meals import Meal
from app.schemas.meals import MealCreate, MealUpdate


def create_meal(db: Session, data: MealCreate) -> Meal:
    meal = Meal(
        user_id=data.user_id,
        name=data.name,
        calories=data.calories,
        protein=data.protein,
        carbs=data.carbs,
        fats=data.fats,
        timestamp=data.timestamp or datetime.utcnow(),
        notes=data.notes,
    )
    db.add(meal)
    db.commit()
    db.refresh(meal)
    return meal


def get_meal(db: Session, meal_id: int) -> Optional[Meal]:
    return db.query(Meal).filter(Meal.id == meal_id).first()


def get_meals_for_user(db: Session, user_id: int) -> List[Meal]:
    return (
        db.query(Meal)
        .filter(Meal.user_id == user_id)
        .order_by(Meal.timestamp.desc())
        .all()
    )


def update_meal(db: Session, meal_id: int, data: MealUpdate) -> Optional[Meal]:
    meal = get_meal(db, meal_id)
    if not meal:
        return None

    for field, value in data.dict(exclude_unset=True).items():
        setattr(meal, field, value)

    db.commit()
    db.refresh(meal)
    return meal


def delete_meal(db: Session, meal_id: int) -> bool:
    meal = get_meal(db, meal_id)
    if not meal:
        return False

    db.delete(meal)
    db.commit()
    return True
