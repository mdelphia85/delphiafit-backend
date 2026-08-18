from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.database.connection import get_db
from app.crud.competition import CompetitionCRUD

router = APIRouter(prefix="/competition", tags=["Competition"])
crud = CompetitionCRUD()


class CompetitionCreate(BaseModel):
    name: str
    description: Optional[str] = None
    sport: Optional[str] = None
    level: Optional[str] = None
    federation_id: Optional[int] = None
    season_id: Optional[int] = None
    is_virtual: Optional[bool] = False


class CompetitionUpdate(BaseModel):
    updates: Dict[str, Any]


@router.post("/create")
def create_competition(data: CompetitionCreate, db: Session = Depends(get_db)):
    return crud.create_competition(db, data.model_dump())


@router.get("/{competition_id:int}")
def get_competition(competition_id: int, db: Session = Depends(get_db)):
    comp = crud.get_competition(db, competition_id)
    if not comp:
        raise HTTPException(status_code=404, detail="Competition not found.")
    return comp


@router.get("/list")
def list_competitions(db: Session = Depends(get_db)):
    return crud.list_competitions(db)


@router.put("/{competition_id}/update")
def update_competition(competition_id: int, data: CompetitionUpdate, db: Session = Depends(get_db)):
    try:
        return crud.update_competition(db, competition_id, data.updates)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{competition_id}/deactivate")
def deactivate_competition(competition_id: int, db: Session = Depends(get_db)):
    try:
        return crud.deactivate_competition(db, competition_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
