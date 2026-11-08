from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.schemas.workout_log import WorkoutLogCreate, WorkoutLog
from app.crud.workout_log import create_workout_log, get_workout_logs
from app.utils.security import get_current_user_id

router = APIRouter(prefix="/workouts", tags=["workouts"])

@router.post("/save", response_model=WorkoutLog)
def save_workout(workout: WorkoutLogCreate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    return create_workout_log(db, user_id, workout)

@router.get("/", response_model=list[WorkoutLog])
def list_workouts(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    return get_workout_logs(db, user_id)
