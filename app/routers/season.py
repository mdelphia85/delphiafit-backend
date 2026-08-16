from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.database import get_db
from app.crud.season import SeasonCRUD

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
def create_season(data: SeasonCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_season(db, data.dict())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Get Season by ID
# ---------------------------------------------------------
@router.get("/{season_id}")
def get_season(season_id: int, db: Session = Depends(get_db)):
    season = crud.get_season(db, season_id)
    if not season:
        raise HTTPException(status_code=404, detail="Season not found.")
    return season


# ---------------------------------------------------------
# List Seasons
# ---------------------------------------------------------
@router.get("/list")
def list_seasons(db: Session = Depends(get_db)):
    return crud.list_seasons(db)


# ---------------------------------------------------------
# Update Season
# ---------------------------------------------------------
@router.put("/{season_id}/update")
def update_season(season_id: int, data: SeasonUpdate, db: Session = Depends(get_db)):
    try:
        return crud.update_season(db, season_id, data.updates)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Deactivate Season
# ---------------------------------------------------------
@router.delete("/{season_id}/deactivate")
def deactivate_season(season_id: int, db: Session = Depends(get_db)):
    try:
        return crud.deactivate_season(db, season_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
