from sqlalchemy.orm import Session
from datetime import datetime

from app.models.disaster import DisasterOperation, DisasterSector, DisasterResource


class DisasterCRUD:

    # Create disaster operation
    def create_operation(self, db: Session, data: dict):
        op = DisasterOperation(
            name=data["name"],
            type=data["type"],
            location=data.get("location"),
            severity=data.get("severity"),
            incident_commander_id=data["incident_commander_id"],
            notes=data.get("notes"),
            started_at=datetime.utcnow()
        )
        db.add(op)
        db.commit()
        db.refresh(op)
        return op

    # List operations
    def list_operations(self, db: Session):
        return db.query(DisasterOperation).all()

    # Get single operation
    def get_operation(self, db: Session, op_id: int):
        return db.query(DisasterOperation).filter(DisasterOperation.id == op_id).first()

    # Close operation
    def close_operation(self, db: Session, op_id: int, status: str = "completed"):
        op = self.get_operation(db, op_id)
        if not op:
            raise ValueError("Operation not found.")
        op.status = status
        op.ended_at = datetime.utcnow()
        db.commit()
        db.refresh(op)
        return op

    # Add sector
    def add_sector(self, db: Session, data: dict):
        sector = DisasterSector(
            operation_id=data["operation_id"],
            name=data["name"],
            description=data.get("description"),
            status=data.get("status", "active")
        )
        db.add(sector)
        db.commit()
        db.refresh(sector)
        return sector

    # List sectors for operation
    def list_sectors(self, db: Session, operation_id: int):
        return db.query(DisasterSector).filter(
            DisasterSector.operation_id == operation_id
        ).all()

    # Add resource
    def add_resource(self, db: Session, data: dict):
        res = DisasterResource(
            operation_id=data["operation_id"],
            resource_type=data["resource_type"],
            quantity=data.get("quantity", 1),
            assigned_sector=data.get("assigned_sector"),
            notes=data.get("notes")
        )
        db.add(res)
        db.commit()
        db.refresh(res)
        return res

    # List resources for operation
    def list_resources(self, db: Session, operation_id: int):
        return db.query(DisasterResource).filter(
            DisasterResource.operation_id == operation_id
        ).all()
