from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.coach import Coach


def create_coach(db: Session, data: dict) -> Coach:
    coach = Coach(**data)
    db.add(coach)
    db.commit()
    db.refresh(coach)
    return coach


def get_coach(db: Session, coach_id: int) -> Optional[Coach]:
    return db.query(Coach).filter(Coach.id == coach_id).first()


def get_coaches(db: Session) -> List[Coach]:
    return db.query(Coach).all()


def update_coach(db: Session, coach_id: int, data: dict) -> Optional[Coach]:
    coach = get_coach(db, coach_id)
    if not coach:
        return None

    for field, value in data.items():
        setattr(coach, field, value)

    db.commit()
    db.refresh(coach)
    return coach


def delete_coach(db: Session, coach_id: int) -> bool:
    coach = get_coach(db, coach_id)
    if not coach:
        return False

    db.delete(coach)
    db.commit()
    return True
