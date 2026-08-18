from sqlalchemy.orm import Session
from datetime import datetime

from app.models.aviation import AviationOperation, AviationCrew, AviationEvent


class AviationCRUD:

    def create_operation(self, db: Session, data: dict):
        op = AviationOperation(
            name=data["name"],
            operation_type=data["operation_type"],
            aircraft=data.get("aircraft"),
            location=data.get("location"),
            mission_commander_id=data["mission_commander_id"],
            notes=data.get("notes"),
            started_at=datetime.utcnow()
        )
        db.add(op)
        db.commit()
        db.refresh(op)
        return op

    def list_operations(self, db: Session):
        return db.query(AviationOperation).all()

    def get_operation(self, db: Session, op_id: int):
        return db.query(AviationOperation).filter(AviationOperation.id == op_id).first()

    def close_operation(self, db: Session, op_id: int, status: str = "completed"):
        op = self.get_operation(db, op_id)
        if not op:
            raise ValueError("Operation not found.")
        op.status = status
        op.ended_at = datetime.utcnow()
        db.commit()
        db.refresh(op)
        return op

    def add_crew(self, db: Session, data: dict):
        crew = AviationCrew(
            operation_id=data["operation_id"],
            role=data["role"],
            member_name=data["member_name"],
            certification=data.get("certification")
        )
        db.add(crew)
        db.commit()
        db.refresh(crew)
        return crew

    def list_crew(self, db: Session, operation_id: int):
        return db.query(AviationCrew).filter(
            AviationCrew.operation_id == operation_id
        ).all()

    def log_event(self, db: Session, data: dict):
        event = AviationEvent(
            operation_id=data["operation_id"],
            event_type=data["event_type"],
            description=data.get("description"),
            severity=data.get("severity"),
            timestamp=datetime.utcnow()
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    def list_events(self, db: Session, operation_id: int):
        return db.query(AviationEvent).filter(
            AviationEvent.operation_id == operation_id
        ).all()
