from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.coach import Coach


class CoachCRUD:

    def create_coach(self, db: Session, email: str, name: str,
                     organization: Optional[str], role: str) -> Coach:
        coach = Coach(
            email=email,
            name=name,
            organization=organization,
            role=role
        )
        db.add(coach)
        db.commit()
        db.refresh(coach)
        return coach

    def get_coach(self, db: Session, coach_id: int) -> Optional[Coach]:
        return db.query(Coach).filter(Coach.id == coach_id).first()

    def get_coach_by_email(self, db: Session, email: str) -> Optional[Coach]:
        return db.query(Coach).filter(Coach.email == email).first()

    def get_coaches(self, db: Session) -> List[Coach]:
        return db.query(Coach).all()

    def update_coach(self, db: Session, coach_id: int, updates: dict) -> Optional[Coach]:
        coach = self.get_coach(db, coach_id)
        if not coach:
            return None

        for field, value in updates.items():
            setattr(coach, field, value)

        db.commit()
        db.refresh(coach)
        return coach

    def delete_coach(self, db: Session, coach_id: int) -> bool:
        coach = self.get_coach(db, coach_id)
        if not coach:
            return False

        db.delete(coach)
        db.commit()
        return True

    # -----------------------------
    # Phase 4 Relationship Endpoints
    # -----------------------------

    def get_coach_teams(self, db: Session, coach_id: int):
        coach = self.get_coach(db, coach_id)
        if not coach:
            return None
        return coach.teams

    def get_coach_clients(self, db: Session, coach_id: int):
        coach = self.get_coach(db, coach_id)
        if not coach:
            return None
        return coach.clients

    def accept_invite(self, db: Session, token: str, name: str):
        # Placeholder — implement once Invite model is aligned
        raise ValueError("Invite acceptance not implemented yet.")
