from sqlalchemy.orm import Session
from app.models.recipes import Recipe
from app.schemas.recipes import RecipeCreate

def create_recipe(db: Session, user_id: int, data: RecipeCreate):
    recipe = Recipe(
        user_id=user_id,
        name=data.name,
        ingredients=data.ingredients,
        instructions=data.instructions,
        calories=data.calories,
        protein=data.protein,
        carbs=data.carbs,
        fats=data.fats
    )
    db.add(recipe)
    db.commit()
    db.refresh(recipe)
    return recipe

def get_recipes(db: Session, user_id: int):
    return db.query(Recipe).filter(Recipe.user_id == user_id).all()

