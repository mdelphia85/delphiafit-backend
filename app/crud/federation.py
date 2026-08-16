from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.federation import Federation


def create_federation(db: Session, data: dict) -> Federation:
    fed = Federation(**data)
    db.add(fed)
    db.commit()
    db.refresh(fed)
    return fed


def get_federation(db: Session, federation_id: int) -> Optional[Federation]:
    return db.query(Federation).filter(Federation.id == federation_id).first()


def get_federations(db: Session) -> List[Federation]:
    return db.query(Federation).all()


def update_federation(db: Session, federation_id: int, data: dict) -> Optional[Federation]:
    fed = get_federation(db, federation_id)
    if not fed:
        return None

    for field, value in data.items():
        setattr(fed, field, value)

    db.commit()
    db.refresh(fed)
    return fed


def delete_federation(db: Session, federation_id: int) -> bool:
    fed = get_federation(db, federation_id)
    if not fed:
        return False

    db.delete(fed)
    db.commit()
    return True
