from sqlalchemy.orm import Session
from datetime import datetime

from app.models.tournament import Tournament


class TournamentCRUD:

    # ---------------------------------------------------------
    # Create Tournament
    # ---------------------------------------------------------
    def create_tournament(self, db: Session, data: dict):
        tournament = Tournament(
            competition_id=data["competition_id"],
            name=data["name"],
            format=data.get("format"),
            rules=data.get("rules"),
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(tournament)
        db.commit()
        db.refresh(tournament)
        return tournament

    # ---------------------------------------------------------
    # Get Tournament by ID
    # ---------------------------------------------------------
    def get_tournament(self, db: Session, tournament_id: int):
        return db.query(Tournament).filter(Tournament.id == tournament_id).first()

    # ---------------------------------------------------------
    # List Tournaments for Competition
    # ---------------------------------------------------------
    def list_tournaments_for_competition(self, db: Session, competition_id: int):
        return db.query(Tournament).filter(
            Tournament.competition_id == competition_id,
            Tournament.is_active == True
        ).all()

    # ---------------------------------------------------------
    # Update Tournament
    # ---------------------------------------------------------
    def update_tournament(self, db: Session, tournament_id: int, updates: dict):
        tournament = self.get_tournament(db, tournament_id)
        if not tournament:
            raise ValueError("Tournament not found.")

        for key, value in updates.items():
            if hasattr(tournament, key):
                setattr(tournament, key, value)

        tournament.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(tournament)
        return tournament

    # ---------------------------------------------------------
    # Deactivate Tournament
    # ---------------------------------------------------------
    def deactivate_tournament(self, db: Session, tournament_id: int):
        tournament = self.get_tournament(db, tournament_id)
        if not tournament:
            raise ValueError("Tournament not found.")

        tournament.is_active = False
        tournament.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(tournament)
        return tournament
