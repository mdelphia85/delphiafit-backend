from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.utils.security import get_current_user_id
from app.schemas.meals import MealCreate, MealRead, MealUpdate
from app.crud.meals import create_meal, get_meals, get_meal, update_meal, delete_meal

router = APIRouter(prefix="/meals", tags=["meals"])

@router.post("/", response_model=MealRead)
def add_meal(payload: MealCreate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    return create_meal(db, user_id, payload)

@router.get("/", response_model=List[MealRead])
def list_meals(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    return get_meals(db, user_id)

@router.put("/{meal_id}", response_model=MealRead)
def edit_meal(meal_id: int, payload: MealUpdate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    meal = get_meal(db, meal_id)
    if not meal or meal.user_id != user_id:
        raise HTTPException(status_code=404, detail="Meal not found")
    return update_meal(db, meal_id, payload)

@router.delete("/{meal_id}")
def remove_meal(meal_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    meal = get_meal(db, meal_id)
    if not meal or meal.user_id != user_id:
        raise HTTPException(status_code=404, detail="Meal not found")
    delete_meal(db, meal_id)
    return {"deleted": True}
