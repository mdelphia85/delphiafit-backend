from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.listing import Listing


def create_listing(db: Session, data: dict) -> Listing:
    listing = Listing(**data)
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing


def get_listing(db: Session, listing_id: int) -> Optional[Listing]:
    return db.query(Listing).filter(Listing.id == listing_id).first()


def get_listings(db: Session) -> List[Listing]:
    return db.query(Listing).all()


def update_listing(db: Session, listing_id: int, data: dict) -> Optional[Listing]:
    listing = get_listing(db, listing_id)
    if not listing:
        return None

    for field, value in data.items():
        setattr(listing, field, value)

    db.commit()
    db.refresh(listing)
    return listing


def delete_listing(db: Session, listing_id: int) -> bool:
    listing = get_listing(db, listing_id)
    if not listing:
        return False

    db.delete(listing)
    db.commit()
    return True
