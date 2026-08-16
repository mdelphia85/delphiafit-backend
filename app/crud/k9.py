from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.k9 import K9


def create_k9(db: Session, data: dict) -> K9:
    k9 = K9(**data)
    db.add(k9)
    db.commit()
    db.refresh(k9)
    return k9


def get_k9(db: Session, k9_id: int) -> Optional[K9]:
    return db.query(K9).filter(K9.id == k9_id).first()


def get_k9_units(db: Session) -> List[K9]:
    return db.query(K9).all()


def update_k9(db: Session, k9_id: int, data: dict) -> Optional[K9]:
    k9 = get_k9(db, k9_id)
    if not k9:
        return None

    for field, value in data.items():
        setattr(k9, field, value)

    db.commit()
    db.refresh(k9)
    return k9


def delete_k9(db: Session, k9_id: int) -> bool:
    k9 = get_k9(db, k9_id)
    if not k9:
        return False

    db.delete(k9)
    db.commit()
    return True
