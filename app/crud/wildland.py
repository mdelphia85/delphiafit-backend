from sqlalchemy.orm import Session
from datetime import datetime

from app.models.wildland import WildlandOperation, WildlandDivision, WildlandResource, WildlandEvent


class WildlandCRUD:

    def create_operation(self, db: Session, data: dict):
        op = WildlandOperation(
            name=data["name"],
            fire_type=data["fire_type"],
            location=data.get("location"),
            containment=data.get("containment", 0.0),
            incident_commander_id=data["incident_commander_id"],
            notes=data.get("notes"),
            started_at=datetime.utcnow()
        )
        db.add(op)
        db.commit()
        db.refresh(op)
        return op

    def list_operations(self, db: Session):
        return db.query(WildlandOperation).all()

    def get_operation(self, db: Session, op_id: int):
        return db.query(WildlandOperation).filter(WildlandOperation.id == op_id).first()

    def update_containment(self, db: Session, op_id: int, containment: float):
        op = self.get_operation(db, op_id)
        if not op:
            raise ValueError("Operation not found.")
        op.containment = containment
        db.commit()
        db.refresh(op)
        return op

    def close_operation(self, db: Session, op_id: int, status="completed"):
        op = self.get_operation(db, op_id)
        if not op:
            raise ValueError("Operation not found.")
        op.status = status
        op.ended_at = datetime.utcnow()
        db.commit()
        db.refresh(op)
        return op

    def add_division(self, db: Session, data: dict):
        div = WildlandDivision(
            operation_id=data["operation_id"],
            name=data["name"],
            status=data.get("status", "active"),
            notes=data.get("notes")
        )
        db.add(div)
        db.commit()
        db.refresh(div)
        return div

    def list_divisions(self, db: Session, operation_id: int):
        return db.query(WildlandDivision).filter(
            WildlandDivision.operation_id == operation_id
        ).all()

    def add_resource(self, db: Session, data: dict):
        res = WildlandResource(
            operation_id=data["operation_id"],
            resource_type=data["resource_type"],
            quantity=data.get("quantity", 1),
            assigned_division=data.get("assigned_division"),
            notes=data.get("notes")
        )
        db.add(res)
        db.commit()
        db.refresh(res)
        return res

    def list_resources(self, db: Session, operation_id: int):
        return db.query(WildlandResource).filter(
            WildlandResource.operation_id == operation_id
        ).all()

    def log_event(self, db: Session, data: dict):
        event = WildlandEvent(
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
        return db.query(WildlandEvent).filter(
            WildlandEvent.operation_id == operation_id
        ).all()
