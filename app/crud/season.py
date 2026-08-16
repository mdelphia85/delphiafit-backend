from sqlalchemy.orm import Session
from datetime import datetime

from app.models.season import Season


class SeasonCRUD:

    # ---------------------------------------------------------
    # Create Season
    # ---------------------------------------------------------
    def create_season(self, db: Session, data: dict):
        season = Season(
            name=data["name"],
            year=data.get("year"),
            sport=data.get("sport"),
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(season)
        db.commit()
        db.refresh(season)
        return season

    # ---------------------------------------------------------
    # Get Season by ID
    # ---------------------------------------------------------
    def get_season(self, db: Session, season_id: int):
        return db.query(Season).filter(Season.id == season_id).first()

    # ---------------------------------------------------------
    # List Seasons
    # ---------------------------------------------------------
    def list_seasons(self, db: Session):
        return db.query(Season).filter(Season.is_active == True).all()

    # ---------------------------------------------------------
    # Update Season
    # ---------------------------------------------------------
    def update_season(self, db: Session, season_id: int, updates: dict):
        season = self.get_season(db, season_id)
        if not season:
            raise ValueError("Season not found.")

        for key, value in updates.items():
            if hasattr(season, key):
                setattr(season, key, value)

        season.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(season)
        return season

    # ---------------------------------------------------------
    # Deactivate Season
    # ---------------------------------------------------------
    def deactivate_season(self, db: Session, season_id: int):
        season = self.get_season(db, season_id)
        if not season:
            raise ValueError("Season not found.")

        season.is_active = False
        season.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(season)
        return season
