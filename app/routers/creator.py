from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.database import get_db
from app.crud.creator import CreatorCRUD

router = APIRouter(prefix="/creator", tags=["Creator"])
crud = CreatorCRUD()


# ---------------------------------------------------------
# Request Models
# ---------------------------------------------------------

class CreatorCreate(BaseModel):
    user_id: int
    name: str
    bio: Optional[str] = None
    expertise: Optional[str] = None
    profile_image: Optional[str] = None


class CreatorUpdate(BaseModel):
    updates: Dict[str, Any]


class RatingCreate(BaseModel):
    user_id: int
    rating: float
    review: Optional[str] = None


# ---------------------------------------------------------
# Create Creator Profile
# ---------------------------------------------------------
@router.post("/create")
def create_creator(data: CreatorCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_creator(db, data.dict())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Get Creator
# ---------------------------------------------------------
@router.get("/{creator_id}")
def get_creator(creator_id: int, db: Session = Depends(get_db)):
    creator = crud.get_creator(db, creator_id)
    if not creator:
        raise HTTPException(status_code=404, detail="Creator not found.")
    return creator


# ---------------------------------------------------------
# List Creators
# ---------------------------------------------------------
@router.get("/list")
def list_creators(db: Session = Depends(get_db)):
    return crud.list_creators(db)


# ---------------------------------------------------------
# Update Creator
# ---------------------------------------------------------
@router.put("/{creator_id}/update")
def update_creator(creator_id: int, data: CreatorUpdate, db: Session = Depends(get_db)):
    try:
        return crud.update_creator(db, creator_id, data.updates)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Deactivate Creator
# ---------------------------------------------------------
@router.delete("/{creator_id}/deactivate")
def deactivate_creator(creator_id: int, db: Session = Depends(get_db)):
    try:
        return crud.deactivate_creator(db, creator_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Add Rating
# ---------------------------------------------------------
@router.post("/{creator_id}/rate")
def rate_creator(creator_id: int, data: RatingCreate, db: Session = Depends(get_db)):
    try:
        return crud.add_rating(db, creator_id, data.user_id, data.rating, data.review)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
