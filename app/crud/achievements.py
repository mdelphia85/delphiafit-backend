from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.achievements import Achievement


def create_achievement(db: Session, data: dict) -> Achievement:
    achievement = Achievement(**data)
    db.add(achievement)
    db.commit()
    db.refresh(achievement)
    return achievement


def get_achievement(db: Session, achievement_id: int) -> Optional[Achievement]:
    return db.query(Achievement).filter(Achievement.id == achievement_id).first()


def get_achievements_for_user(db: Session, user_id: int) -> List[Achievement]:
    return db.query(Achievement).filter(Achievement.user_id == user_id).all()


def update_achievement(db: Session, achievement_id: int, data: dict) -> Optional[Achievement]:
    achievement = get_achievement(db, achievement_id)
    if not achievement:
        return None

    for field, value in data.items():
        setattr(achievement, field, value)

    db.commit()
    db.refresh(achievement)
    return achievement


def delete_achievement(db: Session, achievement_id: int) -> bool:
    achievement = get_achievement(db, achievement_id)
    if not achievement:
        return False

    db.delete(achievement)
    db.commit()
    return True
