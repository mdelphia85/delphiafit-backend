from sqlalchemy.orm import Session
from datetime import datetime

from app.models.creator import Creator
from app.models.rating import Rating


class CreatorCRUD:

    # ---------------------------------------------------------
    # Create Creator Profile
    # ---------------------------------------------------------
    def create_creator(self, db: Session, data: dict):
        creator = Creator(
            user_id=data["user_id"],
            name=data["name"],
            bio=data.get("bio"),
            expertise=data.get("expertise"),
            profile_image=data.get("profile_image"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(creator)
        db.commit()
        db.refresh(creator)
        return creator

    # ---------------------------------------------------------
    # Get Creator by ID
    # ---------------------------------------------------------
    def get_creator(self, db: Session, creator_id: int):
        return db.query(Creator).filter(Creator.id == creator_id).first()

    # ---------------------------------------------------------
    # List All Creators
    # ---------------------------------------------------------
    def list_creators(self, db: Session):
        return db.query(Creator).filter(Creator.is_active == True).all()

    # ---------------------------------------------------------
    # Update Creator Profile
    # ---------------------------------------------------------
    def update_creator(self, db: Session, creator_id: int, updates: dict):
        creator = self.get_creator(db, creator_id)
        if not creator:
            raise ValueError("Creator not found.")

        for key, value in updates.items():
            if hasattr(creator, key):
                setattr(creator, key, value)

        creator.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(creator)
        return creator

    # ---------------------------------------------------------
    # Deactivate Creator
    # ---------------------------------------------------------
    def deactivate_creator(self, db: Session, creator_id: int):
        creator = self.get_creator(db, creator_id)
        if not creator:
            raise ValueError("Creator not found.")

        creator.is_active = False
        creator.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(creator)
        return creator

    # ---------------------------------------------------------
    # Add Rating + Update Aggregates
    # ---------------------------------------------------------
    def add_rating(self, db: Session, creator_id: int, user_id: int, rating: float, review: str = None):
        creator = self.get_creator(db, creator_id)
        if not creator:
            raise ValueError("Creator not found.")

        new_rating = Rating(
            creator_id=creator_id,
            user_id=user_id,
            rating=rating,
            review=review,
            created_at=datetime.utcnow()
        )

        db.add(new_rating)

        # update aggregates
        creator.total_reviews += 1
        creator.average_rating = (
            (creator.average_rating * (creator.total_reviews - 1)) + rating
        ) / creator.total_reviews

        creator.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(creator)
        return creator
