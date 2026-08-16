from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.unit import Unit


def create_unit(db: Session, data: dict) -> Unit:
    unit = Unit(**data)
    db.add(unit)
    db.commit()
    db.refresh(unit)
    return unit


def get_unit(db: Session, unit_id: int) -> Optional[Unit]:
    return db.query(Unit).filter(Unit.id == unit_id).first()


def get_units(db: Session) -> List[Unit]:
    return db.query(Unit).all()


def update_unit(db: Session, unit_id: int, data: dict) -> Optional[Unit]:
    unit = get_unit(db, unit_id)
    if not unit:
        return None

    for field, value in data.items():
        setattr(unit, field, value)

    db.commit()
    db.refresh(unit)
    return unit


def delete_unit(db: Session, unit_id: int) -> bool:
    unit = get_unit(db, unit_id)
    if not unit:
        return False

    db.delete(unit)
    db.commit()
    return True
