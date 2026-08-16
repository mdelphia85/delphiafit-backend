from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.workout_log import WorkoutLogCreate
from app.crud.workout_log import create_workout_log
from app.auth.dependencies import get_current_user

router = APIRouter(
    prefix="/workouts",
    tags=["workouts"]
)

@router.post("/save")
def save_workout(
    workout: WorkoutLogCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    saved = create_workout_log(db, workout, user.id)
    return {"status": "success", "workout": saved}
