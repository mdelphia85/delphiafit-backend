from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.models.certification import Certification, CertificationRequirement, CertificationRecord


class CertificationCRUD:

    # ---------------------------------------------------------
    # Certifications
    # ---------------------------------------------------------
    def create_certification(self, db: Session, data: dict):
        cert = Certification(
            name=data["name"],
            category=data["category"],
            description=data.get("description"),
            required_score=data.get("required_score", 70.0),
            expires_months=data.get("expires_months", 12),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(cert)
        db.commit()
        db.refresh(cert)
        return cert

    def list_certifications(self, db: Session):
        return db.query(Certification).filter(Certification.active == True).all()

    # ---------------------------------------------------------
    # Requirements
    # ---------------------------------------------------------
    def add_requirement(self, db: Session, data: dict):
        req = CertificationRequirement(
            certification_id=data["certification_id"],
            requirement_type=data["requirement_type"],
            target_id=data["target_id"],
            notes=data.get("notes")
        )
        db.add(req)
        db.commit()
        db.refresh(req)
        return req

    def list_requirements(self, db: Session, certification_id: int):
        return db.query(CertificationRequirement).filter(
            CertificationRequirement.certification_id == certification_id
        ).all()

    # ---------------------------------------------------------
    # Records
    # ---------------------------------------------------------
    def issue_certification(self, db: Session, data: dict):
        cert = db.query(Certification).filter(
            Certification.id == data["certification_id"]
        ).first()

        expires_at = datetime.utcnow() + timedelta(days=cert.expires_months * 30)

        record = CertificationRecord(
            user_id=data["user_id"],
            certification_id=data["certification_id"],
            score=data.get("score", 0.0),
            passed=data.get("passed", False),
            issued_at=datetime.utcnow(),
            expires_at=expires_at
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    def list_records(self, db: Session, user_id: int):
        return db.query(CertificationRecord).filter(
            CertificationRecord.user_id == user_id
        ).all()
