from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.database import get_db
from app.crud.tournament import TournamentCRUD

router = APIRouter(prefix="/tournament", tags=["Tournament"])
crud = TournamentCRUD()


# ---------------------------------------------------------
# Request Models
# ---------------------------------------------------------

class TournamentCreate(BaseModel):
    competition_id: int
    name: str
    format: Optional[str] = None
    rules: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class TournamentUpdate(BaseModel):
    updates: Dict[str, Any]


# ---------------------------------------------------------
# Create Tournament
# ---------------------------------------------------------
@router.post("/create")
def create_tournament(data: TournamentCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_tournament(db, data.dict())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Get Tournament by ID
# ---------------------------------------------------------
@router.get("/{tournament_id}")
def get_tournament(tournament_id: int, db: Session = Depends(get_db)):
    tournament = crud.get_tournament(db, tournament_id)
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found.")
    return tournament


# ---------------------------------------------------------
# List Tournaments for Competition
# ---------------------------------------------------------
@router.get("/competition/{competition_id}")
def list_tournaments_for_competition(competition_id: int, db: Session = Depends(get_db)):
    return crud.list_tournaments_for_competition(db, competition_id)


# ---------------------------------------------------------
# Update Tournament
# ---------------------------------------------------------
@router.put("/{tournament_id}/update")
def update_tournament(tournament_id: int, data: TournamentUpdate, db: Session = Depends(get_db)):
    try:
        return crud.update_tournament(db, tournament_id, data.updates)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Deactivate Tournament
# ---------------------------------------------------------
@router.delete("/{tournament_id}/deactivate")
def deactivate_tournament(tournament_id: int, db: Session = Depends(get_db)):
    try:
        return crud.deactivate_tournament(db, tournament_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
