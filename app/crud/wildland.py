from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.wildland import Wildland


def create_wildland(db: Session, data: dict) -> Wildland:
    wl = Wildland(**data)
    db.add(wl)
    db.commit()
    db.refresh(wl)
    return wl


def get_wildland(db: Session, wildland_id: int) -> Optional[Wildland]:
    return db.query(Wildland).filter(Wildland.id == wildland_id).first()


def get_wildland_logs(db: Session) -> List[Wildland]:
    return db.query(Wildland).all()


def update_wildland(db: Session, wildland_id: int, data: dict) -> Optional[Wildland]:
    wl = get_wildland(db, wildland_id)
    if not wl:
        return None

    for field, value in data.items():
        setattr(wl, field, value)

    db.commit()
    db.refresh(wl)
    return wl


def delete_wildland(db: Session, wildland_id: int) -> bool:
    wl = get_wildland(db, wildland_id)
    if not wl:
        return False

    db.delete(wl)
    db.commit()
    return True
