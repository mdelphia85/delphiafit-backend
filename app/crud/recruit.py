from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.recruit import Recruit


def create_recruit(db: Session, data: dict) -> Recruit:
    recruit = Recruit(**data)
    db.add(recruit)
    db.commit()
    db.refresh(recruit)
    return recruit


def get_recruit(db: Session, recruit_id: int) -> Optional[Recruit]:
    return db.query(Recruit).filter(Recruit.id == recruit_id).first()


def get_recruits(db: Session) -> List[Recruit]:
    return db.query(Recruit).all()


def update_recruit(db: Session, recruit_id: int, data: dict) -> Optional[Recruit]:
    recruit = get_recruit(db, recruit_id)
    if not recruit:
        return None

    for field, value in data.items():
        setattr(recruit, field, value)

    db.commit()
    db.refresh(recruit)
    return recruit


def delete_recruit(db: Session, recruit_id: int) -> bool:
    recruit = get_recruit(db, recruit_id)
    if not recruit:
        return False

    db.delete(recruit)
    db.commit()
    return True
