from sqlalchemy.orm import Session
from datetime import datetime

from app.models.maritime import MaritimeOperation, MaritimeCrew, MaritimeIncident


class MaritimeCRUD:

    # ---------------------------------------------------------
    # Create Operation
    # ---------------------------------------------------------
    def create_operation(self, db: Session, data: dict):
        op = MaritimeOperation(
            name=data["name"],
            operation_type=data["operation_type"],
            vessel=data.get("vessel"),
            location=data.get("location"),
            sea_state=data.get("sea_state"),
            commander_id=data["commander_id"],
            notes=data.get("notes"),
            started_at=datetime.utcnow()
        )
        db.add(op)
        db.commit()
        db.refresh(op)
        return op

    # ---------------------------------------------------------
    # List Operations
    # ---------------------------------------------------------
    def list_operations(self, db: Session):
        return db.query(MaritimeOperation).all()

    # ---------------------------------------------------------
    # Get Operation
    # ---------------------------------------------------------
    def get_operation(self, db: Session, op_id: int):
        return db.query(MaritimeOperation).filter(MaritimeOperation.id == op_id).first()

    # ---------------------------------------------------------
    # Close Operation
    # ---------------------------------------------------------
    def close_operation(self, db: Session, op_id: int, status="completed"):
        op = self.get_operation(db, op_id)
        if not op:
            raise ValueError("Operation not found.")
        op.status = status
        op.ended_at = datetime.utcnow()
        db.commit()
        db.refresh(op)
        return op

    # ---------------------------------------------------------
    # Add Crew Member
    # ---------------------------------------------------------
    def add_crew(self, db: Session, data: dict):
        crew = MaritimeCrew(
            operation_id=data["operation_id"],
            role=data["role"],
            member_name=data["member_name"],
            certification=data.get("certification")
        )
        db.add(crew)
        db.commit()
        db.refresh(crew)
        return crew

    # ---------------------------------------------------------
    # List Crew
    # ---------------------------------------------------------
    def list_crew(self, db: Session, operation_id: int):
        return db.query(MaritimeCrew).filter(
            MaritimeCrew.operation_id == operation_id
        ).all()

    # ---------------------------------------------------------
    # Log Incident
    # ---------------------------------------------------------
    def log_incident(self, db: Session, data: dict):
        incident = MaritimeIncident(
            operation_id=data["operation_id"],
            incident_type=data["incident_type"],
            description=data.get("description"),
            severity=data.get("severity"),
            timestamp=datetime.utcnow()
        )
        db.add(incident)
        db.commit()
        db.refresh(incident)
        return incident

    # ---------------------------------------------------------
    # List Incidents
    # ---------------------------------------------------------
    def list_incidents(self, db: Session, operation_id: int):
        return db.query(MaritimeIncident).filter(
            MaritimeIncident.operation_id == operation_id
        ).all()
