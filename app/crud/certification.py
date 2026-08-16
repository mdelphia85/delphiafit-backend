from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.certification import Certification


def create_certification(db: Session, data: dict) -> Certification:
    cert = Certification(**data)
    db.add(cert)
    db.commit()
    db.refresh(cert)
    return cert


def get_certification(db: Session, cert_id: int) -> Optional[Certification]:
    return db.query(Certification).filter(Certification.id == cert_id).first()


def get_certifications_for_user(db: Session, user_id: int) -> List[Certification]:
    return db.query(Certification).filter(Certification.user_id == user_id).all()


def update_certification(db: Session, cert_id: int, data: dict) -> Optional[Certification]:
    cert = get_certification(db, cert_id)
    if not cert:
        return None

    for field, value in data.items():
        setattr(cert, field, value)

    db.commit()
    db.refresh(cert)
    return cert


def delete_certification(db: Session, cert_id: int) -> bool:
    cert = get_certification(db, cert_id)
    if not cert:
        return False

    db.delete(cert)
    db.commit()
    return True
