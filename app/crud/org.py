from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.org import Org


def create_org(db: Session, data: dict) -> Org:
    org = Org(**data)
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


def get_org(db: Session, org_id: int) -> Optional[Org]:
    return db.query(Org).filter(Org.id == org_id).first()


def get_orgs(db: Session) -> List[Org]:
    return db.query(Org).all()


def update_org(db: Session, org_id: int, data: dict) -> Optional[Org]:
    org = get_org(db, org_id)
    if not org:
        return None

    for field, value in data.items():
        setattr(org, field, value)

    db.commit()
    db.refresh(org)
    return org


def delete_org(db: Session, org_id: int) -> bool:
    org = get_org(db, org_id)
    if not org:
        return False

    db.delete(org)
    db.commit()
    return True
