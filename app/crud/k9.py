from sqlalchemy.orm import Session
from datetime import datetime

from app.models.k9 import K9, K9Deployment


class K9CRUD:

    # ---------------------------------------------------------
    # Create K9 Unit
    # ---------------------------------------------------------
    def create_k9(self, db: Session, data: dict):
        k9 = K9(
            name=data["name"],
            breed=data.get("breed"),
            age=data.get("age"),
            agency=data.get("agency"),
            specialty=data.get("specialty"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(k9)
        db.commit()
        db.refresh(k9)
        return k9

    # ---------------------------------------------------------
    # List K9 Units
    # ---------------------------------------------------------
    def list_k9(self, db: Session):
        return db.query(K9).filter(K9.is_active == True).all()

    # ---------------------------------------------------------
    # Log Deployment
    # ---------------------------------------------------------
    def log_deployment(self, db: Session, data: dict):
        deployment = K9Deployment(
            k9_id=data["k9_id"],
            handler_id=data["handler_id"],
            mission_type=data["mission_type"],
            location=data.get("location"),
            notes=data.get("notes"),
            success=data.get("success", False),
            timestamp=datetime.utcnow()
        )

        db.add(deployment)
        db.commit()
        db.refresh(deployment)
        return deployment

    # ---------------------------------------------------------
    # Get Deployment History
    # ---------------------------------------------------------
    def get_history(self, db: Session, k9_id: int):
        return db.query(K9Deployment).filter(
            K9Deployment.k9_id == k9_id
        ).order_by(K9Deployment.timestamp.desc()).all()
