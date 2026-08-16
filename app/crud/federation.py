from sqlalchemy.orm import Session
from datetime import datetime

from app.models.federation import Federation


class FederationCRUD:

    # ---------------------------------------------------------
    # Create Federation
    # ---------------------------------------------------------
    def create_federation(self, db: Session, data: dict):
        federation = Federation(
            name=data["name"],
            country=data.get("country"),
            sport=data.get("sport"),
            rulebook=data.get("rulebook"),
            licensing_requirements=data.get("licensing_requirements"),
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(federation)
        db.commit()
        db.refresh(federation)
        return federation

    # ---------------------------------------------------------
    # Get Federation by ID
    # ---------------------------------------------------------
    def get_federation(self, db: Session, federation_id: int):
        return db.query(Federation).filter(Federation.id == federation_id).first()

    # ---------------------------------------------------------
    # List Federations
    # ---------------------------------------------------------
    def list_federations(self, db: Session):
        return db.query(Federation).filter(Federation.is_active == True).all()

    # ---------------------------------------------------------
    # Update Federation
    # ---------------------------------------------------------
    def update_federation(self, db: Session, federation_id: int, updates: dict):
        federation = self.get_federation(db, federation_id)
        if not federation:
            raise ValueError("Federation not found.")

        for key, value in updates.items():
            if hasattr(federation, key):
                setattr(federation, key, value)

        federation.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(federation)
        return federation

    # ---------------------------------------------------------
    # Update Rulebook
    # ---------------------------------------------------------
    def update_rulebook(self, db: Session, federation_id: int, rulebook: str):
        federation = self.get_federation(db, federation_id)
        if not federation:
            raise ValueError("Federation not found.")

        federation.rulebook = rulebook
        federation.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(federation)
        return federation

    # ---------------------------------------------------------
    # Update Licensing Requirements
    # ---------------------------------------------------------
    def update_licensing(self, db: Session, federation_id: int, licensing: str):
        federation = self.get_federation(db, federation_id)
        if not federation:
            raise ValueError("Federation not found.")

        federation.licensing_requirements = licensing
        federation.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(federation)
        return federation

    # ---------------------------------------------------------
    # Deactivate Federation
    # ---------------------------------------------------------
    def deactivate_federation(self, db: Session, federation_id: int):
        federation = self.get_federation(db, federation_id)
        if not federation:
            raise ValueError("Federation not found.")

        federation.is_active = False
        federation.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(federation)
        return federation
