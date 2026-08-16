from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.clearance import Clearance


def create_clearance(db: Session, data: dict) -> Clearance:
    clearance = Clearance(**data)
    db.add(clearance)
    db.commit()
    db.refresh(clearance)
    return clearance


def get_clearance(db: Session, clearance_id: int) -> Optional[Clearance]:
    return db.query(Clearance).filter(Clearance.id == clearance_id).first()


def get_clearances(db: Session) -> List[Clearance]:
    return db.query(Clearance).all()


def update_clearance(db: Session, clearance_id: int, data: dict) -> Optional[Clearance]:
    clearance = get_clearance(db, clearance_id)
    if not clearance:
        return None

    for field, value in data.items():
        setattr(clearance, field, value)

    db.commit()
    db.refresh(clearance)
    return clearance


def delete_clearance(db: Session, clearance_id: int) -> bool:
    clearance = get_clearance(db, clearance_id)
    if not clearance:
        return False

    db.delete(clearance)
    db.commit()
    return True
