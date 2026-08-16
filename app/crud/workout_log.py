from sqlalchemy.orm import Session
from app.models.workout_log import WorkoutLog
from app.schemas.workout_log import WorkoutLogCreate

def create_workout_log(db: Session, workout: WorkoutLogCreate, user_id: int):
    db_workout = WorkoutLog(
        user_id=user_id,
        mode=workout.mode,
        duration_minutes=workout.duration_minutes,

        # Manual mode fields
        manual_name=workout.manual_name,
        manual_notes=workout.manual_notes,

        # Structured mode fields
        workout_type=workout.workout_type,
        weight_unit=workout.weight_unit,
        weight_value=workout.weight_value,

        # JSON fields
        plan_json=workout.plan_json,
        block_durations_json=workout.block_durations_json,
        equipment_json=workout.equipment_json,
    )

    db.add(db_workout)
    db.commit()
    db.refresh(db_workout)
    return db_workout
