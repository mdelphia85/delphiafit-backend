from sqlalchemy.orm import Session
from datetime import datetime

from app.models.competition import Competition


class CompetitionCRUD:

    def create_competition(self, db: Session, data: dict):
        competition = Competition(
            name=data["name"],
            description=data.get("description"),
            sport=data.get("sport"),
            level=data.get("level"),
            federation_id=data.get("federation_id"),
            season_id=data.get("season_id"),
            is_virtual=data.get("is_virtual", False),
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(competition)
        db.commit()
        db.refresh(competition)
        return competition

    def get_competition(self, db: Session, competition_id: int):
        return db.query(Competition).filter(Competition.id == competition_id).first()

    def list_competitions(self, db: Session):
        return db.query(Competition).filter(Competition.is_active == True).all()

    def update_competition(self, db: Session, competition_id: int, updates: dict):
        comp = self.get_competition(db, competition_id)
        if not comp:
            raise ValueError("Competition not found.")

        for key, value in updates.items():
            if hasattr(comp, key):
                setattr(comp, key, value)

        comp.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(comp)
        return comp

    def deactivate_competition(self, db: Session, competition_id: int):
        comp = self.get_competition(db, competition_id)
        if not comp:
            raise ValueError("Competition not found.")

        comp.is_active = False
        comp.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(comp)
        return comp
