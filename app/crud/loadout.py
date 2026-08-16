from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.loadout import Loadout


def create_loadout(db: Session, data: dict) -> Loadout:
    loadout = Loadout(**data)
    db.add(loadout)
    db.commit()
    db.refresh(loadout)
    return loadout


def get_loadout(db: Session, loadout_id: int) -> Optional[Loadout]:
    return db.query(Loadout).filter(Loadout.id == loadout_id).first()


def get_loadouts(db: Session) -> List[Loadout]:
    return db.query(Loadout).all()


def update_loadout(db: Session, loadout_id: int, data: dict) -> Optional[Loadout]:
    loadout = get_loadout(db, loadout_id)
    if not loadout:
        return None

    for field, value in data.items():
        setattr(loadout, field, value)

    db.commit()
    db.refresh(loadout)
    return loadout


def delete_loadout(db: Session, loadout_id: int) -> bool:
    loadout = get_loadout(db, loadout_id)
    if not loadout:
        return False

    db.delete(loadout)
    db.commit()
    return True
