from sqlalchemy.orm import Session
from datetime import datetime

from app.models.recovery_protocol import RecoveryProtocol
from app.models.recovery_stage import RecoveryStage
from app.models.recovery_progress import RecoveryProgress
from app.models.clearance import Clearance


class MedicalRecoveryCRUD:

    # ---------------------------------------------------------
    # Protocol
    # ---------------------------------------------------------
    def create_protocol(self, db: Session, data: dict):
        protocol = RecoveryProtocol(
            injury_id=data["injury_id"],
            name=data["name"],
            description=data.get("description"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(protocol)
        db.commit()
        db.refresh(protocol)
        return protocol

    def list_protocols(self, db: Session, injury_id: int):
        return db.query(RecoveryProtocol).filter(
            RecoveryProtocol.injury_id == injury_id
        ).all()

    # ---------------------------------------------------------
    # Stages
    # ---------------------------------------------------------
    def add_stage(self, db: Session, data: dict):
        stage = RecoveryStage(
            protocol_id=data["protocol_id"],
            name=data["name"],
            instructions=data.get("instructions"),
            objective_criteria=data.get("objective_criteria"),
            order_index=data["order_index"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(stage)
        db.commit()
        db.refresh(stage)
        return stage

    def list_stages(self, db: Session, protocol_id: int):
        return db.query(RecoveryStage).filter(
            RecoveryStage.protocol_id == protocol_id
        ).order_by(RecoveryStage.order_index).all()

    # ---------------------------------------------------------
    # Progress
    # ---------------------------------------------------------
    def update_progress(self, db: Session, data: dict):
        progress = RecoveryProgress(
            stage_id=data["stage_id"],
            user_id=data["user_id"],
            completed=data.get("completed", False),
            clinician_notes=data.get("clinician_notes"),
            completed_at=datetime.utcnow() if data.get("completed") else None
        )
        db.add(progress)
        db.commit()
        db.refresh(progress)
        return progress

    def get_progress(self, db: Session, stage_id: int, user_id: int):
        return db.query(RecoveryProgress).filter(
            RecoveryProgress.stage_id == stage_id,
            RecoveryProgress.user_id == user_id
        ).all()

    # ---------------------------------------------------------
    # Clearance
    # ---------------------------------------------------------
    def set_clearance(self, db: Session, data: dict):
        clearance = Clearance(
            injury_id=data["injury_id"],
            user_id=data["user_id"],
            clinician_id=data.get("clinician_id"),
            cleared=data["cleared"],
            notes=data.get("notes"),
            cleared_at=datetime.utcnow() if data["cleared"] else None
        )
        db.add(clearance)
        db.commit()
        db.refresh(clearance)
        return clearance

    def get_clearance(self, db: Session, injury_id: int, user_id: int):
        return db.query(Clearance).filter(
            Clearance.injury_id == injury_id,
            Clearance.user_id == user_id
        ).order_by(Clearance.id.desc()).first()
