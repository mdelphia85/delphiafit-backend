from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.rating import Rating


def create_rating(db: Session, data: dict) -> Rating:
    rating = Rating(**data)
    db.add(rating)
    db.commit()
    db.refresh(rating)
    return rating


def get_rating(db: Session, rating_id: int) -> Optional[Rating]:
    return db.query(Rating).filter(Rating.id == rating_id).first()


def get_ratings(db: Session) -> List[Rating]:
    return db.query(Rating).all()


def update_rating(db: Session, rating_id: int, data: dict) -> Optional[Rating]:
    rating = get_rating(db, rating_id)
    if not rating:
        return None

    for field, value in data.items():
        setattr(rating, field, value)

    db.commit()
    db.refresh(rating)
    return rating


def delete_rating(db: Session, rating_id: int) -> bool:
    rating = get_rating(db, rating_id)
    if not rating:
        return False

    db.delete(rating)
    db.commit()
    return True
