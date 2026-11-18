from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.workout_log import WorkoutLog
from app.schemas.workout_log import WorkoutLogCreate, WorkoutLogUpdate


def create_workout_log(db: Session, user_id: int, data: WorkoutLogCreate) -> WorkoutLog:
    log = WorkoutLog(
        user_id=user_id,
        mode=data.mode,
        duration_minutes=data.duration_minutes,
        manual_name=data.manual_name,
        manual_notes=data.manual_notes,
        workout_type=data.workout_type,
        weight_unit=data.weight_unit,
        weight_value=data.weight_value,
        plan_json=data.plan_json,
        block_durations_json=data.block_durations_json,
        equipment_json=data.equipment_json,
        date=data.timestamp if data.timestamp is not None else None,
    )
    if log.date is None:
        from datetime import datetime
        log.date = datetime.utcnow()
    db.add(log); db.commit(); db.refresh(log); return log


def get_workout_log(db: Session, log_id: int) -> Optional[WorkoutLog]:
    return db.query(WorkoutLog).filter(WorkoutLog.id == log_id).first()


def get_workout_logs(db: Session, user_id: int) -> List[WorkoutLog]:
    return db.query(WorkoutLog).filter(WorkoutLog.user_id == user_id).order_by(WorkoutLog.date.desc()).all()


def update_workout_log(db: Session, log_id: int, data: WorkoutLogUpdate) -> Optional[WorkoutLog]:
    log=get_workout_log(db,log_id)
    if not log:return None
    changes=data.model_dump(exclude_unset=True)
    if 'timestamp' in changes:
        changes['date']=changes.pop('timestamp')
    for field,value in changes.items(): setattr(log,field,value)
    db.commit();db.refresh(log);return log


def delete_workout_log(db: Session, log_id: int) -> bool:
    log=get_workout_log(db,log_id)
    if not log:return False
    db.delete(log);db.commit();return True
