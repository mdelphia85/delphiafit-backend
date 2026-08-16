from sqlalchemy.orm import Session
from datetime import datetime

from app.models.hazmat import HazmatOperation, HazmatZone, HazmatResource, HazmatExposure


class HazmatCRUD:

    def create_operation(self, db: Session, data: dict):
        op = HazmatOperation(
            name=data["name"],
            incident_type=data["incident_type"],
            location=data.get("location"),
            threat_level=data.get("threat_level"),
            incident_commander_id=data["incident_commander_id"],
            notes=data.get("notes"),
            started_at=datetime.utcnow()
        )
        db.add(op)
        db.commit()
        db.refresh(op)
        return op

    def list_operations(self, db: Session):
        return db.query(HazmatOperation).all()

    def get_operation(self, db: Session, op_id: int):
        return db.query(HazmatOperation).filter(HazmatOperation.id == op_id).first()

    def close_operation(self, db: Session, op_id: int, status="completed"):
        op = self.get_operation(db, op_id)
        if not op:
            raise ValueError("Operation not found.")
        op.status = status
        op.ended_at = datetime.utcnow()
        db.commit()
        db.refresh(op)
        return op

    def add_zone(self, db: Session, data: dict):
        zone = HazmatZone(
            operation_id=data["operation_id"],
            zone_type=data["zone_type"],
            description=data.get("description"),
            status=data.get("status", "active")
        )
        db.add(zone)
        db.commit()
        db.refresh(zone)
        return zone

    def list_zones(self, db: Session, operation_id: int):
        return db.query(HazmatZone).filter(
            HazmatZone.operation_id == operation_id
        ).all()

    def add_resource(self, db: Session, data: dict):
        res = HazmatResource(
            operation_id=data["operation_id"],
            resource_type=data["resource_type"],
            quantity=data.get("quantity", 1),
            assigned_zone=data.get("assigned_zone"),
            notes=data.get("notes")
        )
        db.add(res)
        db.commit()
        db.refresh(res)
        return res

    def list_resources(self, db: Session, operation_id: int):
        return db.query(HazmatResource).filter(
            HazmatResource.operation_id == operation_id
        ).all()

    def log_exposure(self, db: Session, data: dict):
        exp = HazmatExposure(
            operation_id=data["operation_id"],
            responder_id=data["responder_id"],
            exposure_type=data["exposure_type"],
            severity=data.get("severity"),
            notes=data.get("notes"),
            timestamp=datetime.utcnow()
        )
        db.add(exp)
        db.commit()
        db.refresh(exp)
        return exp

    def list_exposures(self, db: Session, operation_id: int):
        return db.query(HazmatExposure).filter(
            HazmatExposure.operation_id == operation_id
        ).all()
