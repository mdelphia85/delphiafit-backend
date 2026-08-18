from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.enterprise import EnterpriseSettings


def create_enterprise(db: Session, data: dict) -> EnterpriseSettings:
    ent = EnterpriseSettings(**data)
    db.add(ent)
    db.commit()
    db.refresh(ent)
    return ent


def get_enterprise(db: Session, enterprise_id: int) -> Optional[EnterpriseSettings]:
    return db.query(EnterpriseSettings).filter(EnterpriseSettings.id == enterprise_id).first()


def get_enterprises(db: Session) -> List[EnterpriseSettings]:
    return db.query(EnterpriseSettings).all()


def update_enterprise(db: Session, enterprise_id: int, data: dict) -> Optional[EnterpriseSettings]:
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
