from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.database.connection import get_db
from app.crud.ladder import LadderCRUD
from app.crud.competition import CompetitionCRUD
from app.models.ladder import Ladder
from app.models.user import User
from app.utils.security import get_current_user_id

router = APIRouter(prefix="/ladder", tags=["Ladder"])
crud = LadderCRUD()
competition_crud = CompetitionCRUD()


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
def create_ladder(data: LadderCreate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    _require_competition_owner(db, data.competition_id, user_id)
    try:
        return crud.create_ladder(db, data.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Get Ladder by ID
# ---------------------------------------------------------
@router.get("/{ladder_id}")
def get_ladder(ladder_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    ladder = crud.get_ladder(db, ladder_id)
    if not ladder:
        raise HTTPException(status_code=404, detail="Ladder not found.")
    return ladder


# ---------------------------------------------------------
# List Ladders for Competition
# ---------------------------------------------------------
@router.get("/competition/{competition_id}")
def list_ladders_for_competition(competition_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    return crud.list_ladders_for_competition(db, competition_id)


# ---------------------------------------------------------
# Update Ladder
# ---------------------------------------------------------
@router.put("/{ladder_id}/update")
def update_ladder(ladder_id: int, data: LadderUpdate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    _require_ladder_owner(db, ladder_id, user_id)
    try:
        return crud.update_ladder(db, ladder_id, {key: value for key, value in data.updates.items() if key in {"name", "ranking_method", "is_active"}})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Deactivate Ladder
# ---------------------------------------------------------
@router.delete("/{ladder_id}/deactivate")
def deactivate_ladder(ladder_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    _require_ladder_owner(db, ladder_id, user_id)
    try:
        return crud.deactivate_ladder(db, ladder_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


def _require_competition_owner(db: Session, competition_id: int, user_id: int):
    competition = competition_crud.get_competition(db, competition_id)
    user = db.query(User).filter_by(id=user_id).first()
    if not competition:
        raise HTTPException(status_code=404, detail="Competition not found")
    if competition.owner_id != user_id and not (user and user.is_admin):
        raise HTTPException(status_code=403, detail="Not the competition owner")


def _require_ladder_owner(db: Session, ladder_id: int, user_id: int):
    ladder = db.query(Ladder).filter_by(id=ladder_id).first()
    if not ladder:
        raise HTTPException(status_code=404, detail="Ladder not found")
    _require_competition_owner(db, ladder.competition_id, user_id)
