from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.swat import SWAT


def create_swat(db: Session, data: dict) -> SWAT:
    swat = SWAT(**data)
    db.add(swat)
    db.commit()
    db.refresh(swat)
    return swat


def get_swat(db: Session, swat_id: int) -> Optional[SWAT]:
    return db.query(SWAT).filter(SWAT.id == swat_id).first()


def get_swat_units(db: Session) -> List[SWAT]:
    return db.query(SWAT).all()


def update_swat(db: Session, swat_id: int, data: dict) -> Optional[SWAT]:
    swat = get_swat(db, swat_id)
    if not swat:
        return None

    for field, value in data.items():
        setattr(swat, field, value)

    db.commit()
    db.refresh(swat)
    return swat


def delete_swat(db: Session, swat_id: int) -> bool:
    swat = get_swat(db, swat_id)
    if not swat:
        return False

    db.delete(swat)
    db.commit()
    return True
