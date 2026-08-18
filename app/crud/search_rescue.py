from sqlalchemy.orm import Session
from datetime import datetime

from app.models.search_rescue import SearchRescue, SARTeam, SARVictim


class SearchRescueCRUD:

    # ---------------------------------------------------------
    # Create Operation
    # ---------------------------------------------------------
    def create_operation(self, db: Session, data: dict):
        op = SearchRescue(
            operation_name=data["operation_name"],
            operation_type=data["operation_type"],
            location=data.get("location"),
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
        return db.query(SearchRescue).all()

    # ---------------------------------------------------------
    # Add Team
    # ---------------------------------------------------------
    def add_team(self, db: Session, data: dict):
        team = SARTeam(
            operation_id=data["operation_id"],
            team_name=data["team_name"],
            members=data.get("members"),
            specialty=data.get("specialty")
        )
        db.add(team)
        db.commit()
        db.refresh(team)
        return team

    # ---------------------------------------------------------
    # Add Victim
    # ---------------------------------------------------------
    def add_victim(self, db: Session, data: dict):
        victim = SARVictim(
            operation_id=data["operation_id"],
            name=data.get("name"),
            condition=data.get("condition"),
            found_at=data.get("found_at"),
            extraction_time=data.get("extraction_time"),
            notes=data.get("notes")
        )
        db.add(victim)
        db.commit()
        db.refresh(victim)
        return victim

    # ---------------------------------------------------------
    # Get Operation Details
    # ---------------------------------------------------------
    def get_operation(self, db: Session, op_id: int):
        return db.query(SearchRescue).filter(SearchRescue.id == op_id).first()
