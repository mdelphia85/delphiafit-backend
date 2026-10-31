from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.database.connection import get_db
from app.crud.tournament import TournamentCRUD
from app.crud.competition import CompetitionCRUD
from app.models.user import User
from app.utils.security import get_current_user_id

router = APIRouter(prefix="/tournament", tags=["Tournament"])
crud = TournamentCRUD()
competition_crud = CompetitionCRUD()


# ---------------------------------------------------------
# Request Models
# ---------------------------------------------------------

class TournamentCreate(BaseModel):
    competition_id: int
    name: str
    format: Optional[str] = None
    rules: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class TournamentUpdate(BaseModel):
    updates: Dict[str, Any]


# ---------------------------------------------------------
# Create Tournament
# ---------------------------------------------------------
@router.post("/create")
def create_tournament(data: TournamentCreate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    competition = competition_crud.get_competition(db, data.competition_id)
    user = db.query(User).filter_by(id=user_id).first()
    if not competition:
        raise HTTPException(status_code=404, detail="Competition not found")
    if competition.owner_id != user_id and not (user and user.is_admin):
        raise HTTPException(status_code=403, detail="Not the competition owner")
    try:
        return crud.create_tournament(db, data.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Get Tournament by ID
# ---------------------------------------------------------
@router.get("/{tournament_id}")
def get_tournament(tournament_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    tournament = crud.get_tournament(db, tournament_id)
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found.")
    return tournament


# ---------------------------------------------------------
# List Tournaments for Competition
# ---------------------------------------------------------
@router.get("/competition/{competition_id}")
def list_tournaments_for_competition(competition_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    return crud.list_tournaments_for_competition(db, competition_id)


# ---------------------------------------------------------
# Update Tournament
# ---------------------------------------------------------
@router.put("/{tournament_id}/update")
def update_tournament(tournament_id: int, data: TournamentUpdate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    _require_tournament_owner(db, tournament_id, user_id)
    try:
        return crud.update_tournament(db, tournament_id, {key: value for key, value in data.updates.items() if key in {"name", "format", "rules", "start_date", "end_date", "is_active"}})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Deactivate Tournament
# ---------------------------------------------------------
@router.delete("/{tournament_id}/deactivate")
def deactivate_tournament(tournament_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    _require_tournament_owner(db, tournament_id, user_id)
    try:
        return crud.deactivate_tournament(db, tournament_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


def _require_tournament_owner(db: Session, tournament_id: int, user_id: int):
    tournament = crud.get_tournament(db, tournament_id)
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    competition = competition_crud.get_competition(db, tournament.competition_id)
    user = db.query(User).filter_by(id=user_id).first()
    if competition.owner_id != user_id and not (user and user.is_admin):
        raise HTTPException(status_code=403, detail="Not the tournament owner")
