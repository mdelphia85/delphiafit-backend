from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.database.connection import get_db
from app.crud.creator import CreatorCRUD
from app.models.creator import Creator
from app.models.listing import Listing
from app.models.rating import Rating
from app.models.community_area import ListingInterest
from app.models.user import User
from app.utils.security import get_current_user_id

router = APIRouter(prefix="/creator", tags=["Creator"])
crud = CreatorCRUD()


# ---------------------------------------------------------
# Request Models
# ---------------------------------------------------------

class CreatorCreate(BaseModel):
    user_id: Optional[int] = None
    name: str
    bio: Optional[str] = None
    expertise: Optional[str] = None
    profile_image: Optional[str] = None


class CreatorUpdate(BaseModel):
    updates: Dict[str, Any]


class RatingCreate(BaseModel):
    rating: float
    review: Optional[str] = None


# ---------------------------------------------------------
# Create Creator Profile
# ---------------------------------------------------------
@router.post("/create")
def create_creator(data: CreatorCreate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    if data.user_id is not None and data.user_id != user_id:
        raise HTTPException(status_code=403, detail="Cannot create another user's creator profile")
    payload = data.model_dump(exclude={"user_id"})
    payload["user_id"] = user_id
    try:
        existing = db.query(Creator).filter_by(user_id=user_id, is_active=True).first()
        return existing or crud.create_creator(db, payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Get Creator
# ---------------------------------------------------------
@router.get("/{creator_id:int}")
def get_creator(creator_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    creator = crud.get_creator(db, creator_id)
    if not creator:
        raise HTTPException(status_code=404, detail="Creator not found.")
    return creator


# ---------------------------------------------------------
# List Creators
# ---------------------------------------------------------
@router.get("/list")
def list_creators(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    return crud.list_creators(db)


# ---------------------------------------------------------
# Update Creator
# ---------------------------------------------------------
@router.put("/{creator_id}/update")
def update_creator(creator_id: int, data: CreatorUpdate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    creator = crud.get_creator(db, creator_id)
    if not creator:
        raise HTTPException(status_code=404, detail="Creator not found")
    if creator.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not the creator profile owner")
    try:
        updates = {key: value for key, value in data.updates.items() if key in {"name", "bio", "expertise", "profile_image"}}
        return crud.update_creator(db, creator_id, updates)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Deactivate Creator
# ---------------------------------------------------------
@router.delete("/{creator_id}/deactivate")
def deactivate_creator(creator_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    creator = crud.get_creator(db, creator_id)
    if not creator:
        raise HTTPException(status_code=404, detail="Creator not found")
    if creator.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not the creator profile owner")
    try:
        return crud.deactivate_creator(db, creator_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Add Rating
# ---------------------------------------------------------
@router.post("/{creator_id}/rate")
def rate_creator(creator_id: int, data: RatingCreate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    try:
        return crud.add_rating(db, creator_id, user_id, data.rating, data.review)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class MarketplaceListingCreate(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    price: float = 0


class MarketplaceInterestCreate(BaseModel):
    message: Optional[str] = None


@router.get("/marketplace/listings")
def list_marketplace_listings(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    rows = db.query(Listing, Creator, User.name).join(Creator, Creator.id == Listing.creator_id).join(User, User.id == Creator.user_id).filter(Listing.is_active.is_(True)).order_by(Listing.created_at.desc()).all()
    return [{"id": listing.id, "creator_id": creator.id, "creator_user_id": creator.user_id,
             "title": listing.title, "description": listing.description, "category": listing.category,
             "price": listing.price, "creator_name": creator.name or name}
            for listing, creator, name in rows]


@router.post("/marketplace/listings")
def create_marketplace_listing(data: MarketplaceListingCreate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    creator = db.query(Creator).filter_by(user_id=user_id, is_active=True).first()
    if creator is None:
        user = db.query(User).filter_by(id=user_id).first()
        creator = Creator(user_id=user_id, name=user.name, is_active=True)
        db.add(creator)
        db.flush()
    row = Listing(creator_id=creator.id, title=data.title.strip(), description=data.description,
                  category=data.category, price=max(0, data.price), is_active=True)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.put("/marketplace/listings/{listing_id}")
def update_marketplace_listing(listing_id: int, data: MarketplaceListingCreate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    row = db.query(Listing).filter_by(id=listing_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Listing not found")
    creator = db.query(Creator).filter_by(id=row.creator_id).first()
    if creator.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not the listing owner")
    row.title, row.description, row.category, row.price = data.title.strip(), data.description, data.category, max(0, data.price)
    row.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(row)
    return row


@router.post("/marketplace/listings/{listing_id}/interest")
def request_listing_access(listing_id: int, data: MarketplaceInterestCreate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    listing = db.query(Listing).filter_by(id=listing_id, is_active=True).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    creator = db.query(Creator).filter_by(id=listing.creator_id).first()
    if creator.user_id == user_id:
        raise HTTPException(status_code=400, detail="Creators cannot request their own listing")
    row = db.query(ListingInterest).filter_by(listing_id=listing_id, user_id=user_id).first()
    if row is None:
        row = ListingInterest(listing_id=listing_id, user_id=user_id, message=data.message)
        db.add(row)
    elif data.message is not None:
        row.message = data.message
    db.commit()
    return {"listing_id": listing_id, "requested": True}


@router.get("/marketplace/interests")
def list_listing_interests(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    return [{"id": interest.id, "listing_id": interest.listing_id, "message": interest.message,
             "created_at": interest.created_at}
            for interest in db.query(ListingInterest).filter_by(user_id=user_id).all()]


@router.get("/marketplace/listings/{listing_id}/interests")
def list_listing_owner_interests(listing_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    listing = db.query(Listing).filter_by(id=listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    creator = db.query(Creator).filter_by(id=listing.creator_id).first()
    if creator.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not the listing owner")
    rows = db.query(ListingInterest, User.name).join(User, User.id == ListingInterest.user_id).filter(ListingInterest.listing_id == listing_id).all()
    return [{"user_id": row.user_id, "name": name, "message": row.message, "created_at": row.created_at} for row, name in rows]
