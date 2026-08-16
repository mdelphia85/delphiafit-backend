from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.enterprise import Enterprise


def create_enterprise(db: Session, data: dict) -> Enterprise:
    ent = Enterprise(**data)
    db.add(ent)
    db.commit()
    db.refresh(ent)
    return ent


def get_enterprise(db: Session, enterprise_id: int) -> Optional[Enterprise]:
    return db.query(Enterprise).filter(Enterprise.id == enterprise_id).first()


def get_enterprises(db: Session) -> List[Enterprise]:
    return db.query(Enterprise).all()


def update_enterprise(db: Session, enterprise_id: int, data: dict) -> Optional[Enterprise]:
    ent = get_enterprise(db, enterprise_id)
    if not ent:
        return None

    for field, value in data.items():
        setattr(ent, field, value)

    db.commit()
    db.refresh(ent)
    return ent


def delete_enterprise(db: Session, enterprise_id: int) -> bool:
    ent = get_enterprise(db, enterprise_id)
    if not ent:
        return False

    db.delete(ent)
    db.commit()
    return True
