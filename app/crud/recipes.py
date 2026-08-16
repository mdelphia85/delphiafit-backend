from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.recipes import Recipe
from app.schemas.recipes import RecipeCreate, RecipeUpdate


def create_recipe(db: Session, data: RecipeCreate) -> Recipe:
    recipe = Recipe(
        user_id=data.user_id,
        name=data.name,
        ingredients=data.ingredients,
        instructions=data.instructions,
        calories=data.calories,
        protein=data.protein,
        carbs=data.carbs,
        fats=data.fats,
    )
    db.add(recipe)
    db.commit()
    db.refresh(recipe)
    return recipe


def get_recipe(db: Session, recipe_id: int) -> Optional[Recipe]:
    return db.query(Recipe).filter(Recipe.id == recipe_id).first()


def get_recipes_for_user(db: Session, user_id: int) -> List[Recipe]:
    return db.query(Recipe).filter(Recipe.user_id == user_id).all()


def update_recipe(db: Session, recipe_id: int, data: RecipeUpdate) -> Optional[Recipe]:
    recipe = get_recipe(db, recipe_id)
    if not recipe:
        return None

    for field, value in data.dict(exclude_unset=True).items():
        setattr(recipe, field, value)

    db.commit()
    db.refresh(recipe)
    return recipe


def delete_recipe(db: Session, recipe_id: int) -> bool:
    recipe = get_recipe(db, recipe_id)
    if not recipe:
        return False

    db.delete(recipe)
    db.commit()
    return True
