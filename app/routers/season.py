from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.database.connection import get_db
from app.crud.season import SeasonCRUD
from app.models.creator import Creator
from app.models.user import User
from app.utils.security import get_current_user_id

router = APIRouter(prefix="/season", tags=["Season"])
crud = SeasonCRUD()


# ---------------------------------------------------------
# Request Models
# ---------------------------------------------------------

class SeasonCreate(BaseModel):
    name: str
    year: Optional[int] = None
    sport: Optional[str] = None


class SeasonUpdate(BaseModel):
    updates: Dict[str, Any]


# ---------------------------------------------------------
# Create Season
# ---------------------------------------------------------
@router.post("/create")
def create_season(data: SeasonCreate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    if not _can_create(db, user_id):
        raise HTTPException(status_code=403, detail="An active creator profile or administrator role is required")
    try:
        row = crud.create_season(db, data.model_dump())
        row.owner_id = user_id
        db.commit()
        db.refresh(row)
        return row
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Get Season by ID
# ---------------------------------------------------------
@router.get("/{season_id:int}")
def get_season(season_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    season = crud.get_season(db, season_id)
    if not season:
        raise HTTPException(status_code=404, detail="Season not found.")
    return season


# ---------------------------------------------------------
# List Seasons
# ---------------------------------------------------------
@router.get("/list")
def list_seasons(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    return crud.list_seasons(db)


# ---------------------------------------------------------
# Update Season
# ---------------------------------------------------------
@router.put("/{season_id}/update")
def update_season(season_id: int, data: SeasonUpdate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    _require_owner(db, season_id, user_id)
    try:
        return crud.update_season(db, season_id, {key: value for key, value in data.updates.items() if key in {"name", "year", "sport", "is_active"}})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Deactivate Season
# ---------------------------------------------------------
@router.delete("/{season_id}/deactivate")
def deactivate_season(season_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    _require_owner(db, season_id, user_id)
    try:
        return crud.deactivate_season(db, season_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


def _can_create(db: Session, user_id: int) -> bool:
    user = db.query(User).filter_by(id=user_id).first()
    return bool(user and user.is_admin) or db.query(Creator).filter_by(user_id=user_id, is_active=True).first() is not None


def _require_owner(db: Session, season_id: int, user_id: int):
    row = crud.get_season(db, season_id)
    user = db.query(User).filter_by(id=user_id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Season not found")
    if row.owner_id != user_id and not (user and user.is_admin):
        raise HTTPException(status_code=403, detail="Not the season owner")
