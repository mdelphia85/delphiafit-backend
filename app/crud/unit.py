from sqlalchemy.orm import Session
from datetime import datetime

from app.models.unit import Unit, UnitMember, UnitCapability


class UnitCRUD:

    # ---------------------------------------------------------
    # Units
    # ---------------------------------------------------------
    def create_unit(self, db: Session, data: dict):
        unit = Unit(
            name=data["name"],
            unit_type=data["unit_type"],
            description=data.get("description"),
            readiness_score=0.0,
            active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(unit)
        db.commit()
        db.refresh(unit)
        return unit

    def list_units(self, db: Session):
        return db.query(Unit).filter(Unit.active == True).all()

    def get_unit(self, db: Session, unit_id: int):
        return db.query(Unit).filter(Unit.id == unit_id).first()

    # ---------------------------------------------------------
    # Members
    # ---------------------------------------------------------
    def add_member(self, db: Session, data: dict):
        member = UnitMember(
            unit_id=data["unit_id"],
            user_id=data["user_id"],
            role=data["role"],
            notes=data.get("notes")
        )
        db.add(member)
        db.commit()
        db.refresh(member)
        return member

    def list_members(self, db: Session, unit_id: int):
        return db.query(UnitMember).filter(
            UnitMember.unit_id == unit_id
        ).all()

    # ---------------------------------------------------------
    # Capabilities
    # ---------------------------------------------------------
    def add_capability(self, db: Session, data: dict):
        cap = UnitCapability(
            unit_id=data["unit_id"],
            capability=data["capability"],
            score=data.get("score", 0.0),
            notes=data.get("notes")
        )
        db.add(cap)
        db.commit()
        db.refresh(cap)
        return cap

    def list_capabilities(self, db: Session, unit_id: int):
        return db.query(UnitCapability).filter(
            UnitCapability.unit_id == unit_id
        ).all()

    # ---------------------------------------------------------
    # Update readiness
    # ---------------------------------------------------------
    def update_readiness(self, db: Session, unit_id: int, readiness_score: float):
        unit = self.get_unit(db, unit_id)
        unit.readiness_score = readiness_score
        unit.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(unit)
        return unit
