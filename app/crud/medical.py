from sqlalchemy.orm import Session
from datetime import datetime

from app.models.injury import Injury
from app.models.pt import PTPlan
from app.models.recovery import RecoveryProtocol


class MedicalCRUD:

    # ---------------------------------------------------------
    # Injury Logging
    # ---------------------------------------------------------
    def log_injury(self, db: Session, data: dict):
        injury = Injury(
            user_id=data["user_id"],
            type=data["type"],
            severity=data["severity"],
            description=data.get("description"),
            occurred_at=data["occurred_at"],
            resolved=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(injury)
        db.commit()
        db.refresh(injury)
        return injury

    def get_injury(self, db: Session, injury_id: int):
        return db.query(Injury).filter(Injury.id == injury_id).first()

    def list_injuries(self, db: Session, user_id: int):
        return db.query(Injury).filter(Injury.user_id == user_id).all()

    def resolve_injury(self, db: Session, injury_id: int):
        injury = self.get_injury(db, injury_id)
        if not injury:
            raise ValueError("Injury not found.")

        injury.resolved = True
        injury.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(injury)
        return injury

    # ---------------------------------------------------------
    # PT Plans
    # ---------------------------------------------------------
    def create_pt_plan(self, db: Session, data: dict):
        plan = PTPlan(
            injury_id=data["injury_id"],
            name=data["name"],
            description=data.get("description"),
            frequency_per_week=data.get("frequency_per_week", 3),
            duration_weeks=data.get("duration_weeks", 4),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(plan)
        db.commit()
        db.refresh(plan)
        return plan

    def list_pt_plans(self, db: Session, injury_id: int):
        return db.query(PTPlan).filter(PTPlan.injury_id == injury_id).all()

    # ---------------------------------------------------------
    # Recovery Protocols
    # ---------------------------------------------------------
    def create_recovery_protocol(self, db: Session, data: dict):
        protocol = RecoveryProtocol(
            injury_id=data["injury_id"],
            stage=data["stage"],
            instructions=data.get("instructions"),
            return_to_play_clearance=data.get("return_to_play_clearance", False),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(protocol)
        db.commit()
        db.refresh(protocol)
        return protocol

    def list_recovery_protocols(self, db: Session, injury_id: int):
        return db.query(RecoveryProtocol).filter(
            RecoveryProtocol.injury_id == injury_id
        ).all()
