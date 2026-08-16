from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.schedule import Schedule


def create_schedule(db: Session, data: dict) -> Schedule:
    sched = Schedule(**data)
    db.add(sched)
    db.commit()
    db.refresh(sched)
    return sched


def get_schedule(db: Session, schedule_id: int) -> Optional[Schedule]:
    return db.query(Schedule).filter(Schedule.id == schedule_id).first()


def get_schedules(db: Session) -> List[Schedule]:
    return db.query(Schedule).all()


def update_schedule(db: Session, schedule_id: int, data: dict) -> Optional[Schedule]:
    sched = get_schedule(db, schedule_id)
    if not sched:
        return None

    for field, value in data.items():
        setattr(sched, field, value)

    db.commit()
    db.refresh(sched)
    return sched


def delete_schedule(db: Session, schedule_id: int) -> bool:
    sched = get_schedule(db, schedule_id)
    if not sched:
        return False

    db.delete(sched)
    db.commit()
    return True
