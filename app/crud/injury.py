from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.injury import Injury


def create_injury(db: Session, data: dict) -> Injury:
    injury = Injury(**data)
    db.add(injury)
    db.commit()
    db.refresh(injury)
    return injury


def get_injury(db: Session, injury_id: int) -> Optional[Injury]:
    return db.query(Injury).filter(Injury.id == injury_id).first()


def get_injuries_for_user(db: Session, user_id: int) -> List[Injury]:
    return db.query(Injury).filter(Injury.user_id == user_id).all()


def update_injury(db: Session, injury_id: int, data: dict) -> Optional[Injury]:
    injury = get_injury(db, injury_id)
    if not injury:
        return None

    for field, value in data.items():
        setattr(injury, field, value)

    db.commit()
    db.refresh(injury)
    return injury


def delete_injury(db: Session, injury_id: int) -> bool:
    injury = get_injury(db, injury_id)
    if not injury:
        return False

    db.delete(injury)
    db.commit()
    return True
