from sqlalchemy.orm import Session
from datetime import datetime

from app.models.loadout import Loadout, LoadoutItem


class LoadoutCRUD:

    # ---------------------------------------------------------
    # Loadouts
    # ---------------------------------------------------------
    def create_loadout(self, db: Session, data: dict):
        loadout = Loadout(
            user_id=data["user_id"],
            name=data["name"],
            category=data["category"],
            description=data.get("description"),
            total_weight=0.0,
            mobility_score=1.0,
            endurance_score=1.0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(loadout)
        db.commit()
        db.refresh(loadout)
        return loadout

    def list_loadouts(self, db: Session, user_id: int):
        return db.query(Loadout).filter(
            Loadout.user_id == user_id
        ).all()

    def get_loadout(self, db: Session, loadout_id: int):
        return db.query(Loadout).filter(
            Loadout.id == loadout_id
        ).first()

    # ---------------------------------------------------------
    # Items
    # ---------------------------------------------------------
    def add_item(self, db: Session, data: dict):
        item = LoadoutItem(
            loadout_id=data["loadout_id"],
            name=data["name"],
            weight=data.get("weight", 0.0),
            quantity=data.get("quantity", 1),
            notes=data.get("notes")
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    def list_items(self, db: Session, loadout_id: int):
        return db.query(LoadoutItem).filter(
            LoadoutItem.loadout_id == loadout_id
        ).all()

    # ---------------------------------------------------------
    # Update loadout totals
    # ---------------------------------------------------------
    def update_totals(self, db: Session, loadout_id: int, total_weight: float,
                      mobility_score: float, endurance_score: float):
        loadout = self.get_loadout(db, loadout_id)
        loadout.total_weight = total_weight
        loadout.mobility_score = mobility_score
        loadout.endurance_score = endurance_score
        loadout.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(loadout)
        return loadout
