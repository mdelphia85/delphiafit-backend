from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.ladder import Ladder


def create_ladder(db: Session, data: dict) -> Ladder:
    ladder = Ladder(**data)
    db.add(ladder)
    db.commit()
    db.refresh(ladder)
    return ladder


def get_ladder(db: Session, ladder_id: int) -> Optional[Ladder]:
    return db.query(Ladder).filter(Ladder.id == ladder_id).first()


def get_ladders(db: Session) -> List[Ladder]:
    return db.query(Ladder).all()


def update_ladder(db: Session, ladder_id: int, data: dict) -> Optional[Ladder]:
    ladder = get_ladder(db, ladder_id)
    if not ladder:
        return None

    for field, value in data.items():
        setattr(ladder, field, value)

    db.commit()
    db.refresh(ladder)
    return ladder


def delete_ladder(db: Session, ladder_id: int) -> bool:
    ladder = get_ladder(db, ladder_id)
    if not ladder:
        return False

    db.delete(ladder)
    db.commit()
    return True

