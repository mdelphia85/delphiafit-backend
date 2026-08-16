from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.macros import Macros
from app.schemas.macros import MacrosCreate, MacrosUpdate


def create_macros(db: Session, data: MacrosCreate) -> Macros:
    macros = Macros(
        user_id=data.user_id,
        protein=data.protein,
        carbs=data.carbs,
        fats=data.fats,
        calories=data.calories,
        timestamp=data.timestamp or datetime.utcnow(),
    )
    db.add(macros)
    db.commit()
    db.refresh(macros)
    return macros


def get_macros(db: Session, macros_id: int) -> Optional[Macros]:
    return db.query(Macros).filter(Macros.id == macros_id).first()


def get_macros_for_user(db: Session, user_id: int) -> List[Macros]:
    return (
        db.query(Macros)
        .filter(Macros.user_id == user_id)
        .order_by(Macros.timestamp.desc())
        .all()
    )


def update_macros(db: Session, macros_id: int, data: MacrosUpdate) -> Optional[Macros]:
    macros = get_macros(db, macros_id)
    if not macros:
        return None

    for field, value in data.dict(exclude_unset=True).items():
        setattr(macros, field, value)

    db.commit()
    db.refresh(macros)
    return macros


def delete_macros(db: Session, macros_id: int) -> bool:
    macros = get_macros(db, macros_id)
    if not macros:
        return False

    db.delete(macros)
    db.commit()
    return True
