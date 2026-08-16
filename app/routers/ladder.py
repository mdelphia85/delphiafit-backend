from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.database import get_db
from app.crud.ladder import LadderCRUD

router = APIRouter(prefix="/ladder", tags=["Ladder"])
crud = LadderCRUD()


# ---------------------------------------------------------
# Request Models
# ---------------------------------------------------------

class LadderCreate(BaseModel):
    competition_id: int
    name: str
    ranking_method: Optional[str] = "elo"


class LadderUpdate(BaseModel):
    updates: Dict[str, Any]


# ---------------------------------------------------------
# Create Ladder
# ---------------------------------------------------------
@router.post("/create")
def create_ladder(data: LadderCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_ladder(db, data.dict())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Get Ladder by ID
# ---------------------------------------------------------
@router.get("/{ladder_id}")
def get_ladder(ladder_id: int, db: Session = Depends(get_db)):
    ladder = crud.get_ladder(db, ladder_id)
    if not ladder:
        raise HTTPException(status_code=404, detail="Ladder not found.")
    return ladder


# ---------------------------------------------------------
# List Ladders for Competition
# ---------------------------------------------------------
@router.get("/competition/{competition_id}")
def list_ladders_for_competition(competition_id: int, db: Session = Depends(get_db)):
    return crud.list_ladders_for_competition(db, competition_id)


# ---------------------------------------------------------
# Update Ladder
# ---------------------------------------------------------
@router.put("/{ladder_id}/update")
def update_ladder(ladder_id: int, data: LadderUpdate, db: Session = Depends(get_db)):
    try:
        return crud.update_ladder(db, ladder_id, data.updates)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Deactivate Ladder
# ---------------------------------------------------------
@router.delete("/{ladder_id}/deactivate")
def deactivate_ladder(ladder_id: int, db: Session = Depends(get_db)):
    try:
        return crud.deactivate_ladder(db, ladder_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
