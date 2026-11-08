from sqlalchemy.orm import Session
from datetime import datetime

from app.models.ladder import Ladder


class LadderCRUD:

    # ---------------------------------------------------------
    # Create Ladder
    # ---------------------------------------------------------
    def create_ladder(self, db: Session, data: dict):
        ladder = Ladder(
            competition_id=data["competition_id"],
            name=data["name"],
            ranking_method=data.get("ranking_method", "elo"),
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(ladder)
        db.commit()
        db.refresh(ladder)
        return ladder

    # ---------------------------------------------------------
    # Get Ladder by ID
    # ---------------------------------------------------------
    def get_ladder(self, db: Session, ladder_id: int):
        return db.query(Ladder).filter(Ladder.id == ladder_id).first()

    # ---------------------------------------------------------
    # List Ladders for Competition
    # ---------------------------------------------------------
    def list_ladders_for_competition(self, db: Session, competition_id: int):
        return db.query(Ladder).filter(
            Ladder.competition_id == competition_id,
            Ladder.is_active == True
        ).all()

    # ---------------------------------------------------------
    # Update Ladder
    # ---------------------------------------------------------
    def update_ladder(self, db: Session, ladder_id: int, updates: dict):
        ladder = self.get_ladder(db, ladder_id)
        if not ladder:
            raise ValueError("Ladder not found.")

        for key, value in updates.items():
            if hasattr(ladder, key):
                setattr(ladder, key, value)

        ladder.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(ladder)
        return ladder

    # ---------------------------------------------------------
    # Deactivate Ladder
    # ---------------------------------------------------------
    def deactivate_ladder(self, db: Session, ladder_id: int):
        ladder = self.get_ladder(db, ladder_id)
        if not ladder:
            raise ValueError("Ladder not found.")

        ladder.is_active = False
        ladder.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(ladder)
        return ladder
