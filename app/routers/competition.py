from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.database.connection import get_db
from app.crud.competition import CompetitionCRUD
from app.models.community_area import CompetitionRegistration
from app.models.user import User
from app.models.creator import Creator
from app.models.community_area import FederationMembership
from app.models.season import Season
from app.utils.security import get_current_user_id

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


def _is_competition_creator(db: Session, user_id: int) -> bool:
    user = db.query(User).filter_by(id=user_id).first()
    return bool(user and user.is_admin) or db.query(Creator).filter_by(user_id=user_id, is_active=True).first() is not None


@router.post("/create")
def create_competition(data: CompetitionCreate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    if not _is_competition_creator(db, user_id):
        raise HTTPException(status_code=403, detail="An active creator profile or administrator role is required")
    user = db.query(User).filter_by(id=user_id).first()
    if data.federation_id is not None and not (user and user.is_admin) and not db.query(FederationMembership).filter_by(federation_id=data.federation_id, user_id=user_id).first():
        raise HTTPException(status_code=404, detail="Federation membership required")
    if data.season_id is not None:
        season = db.query(Season).filter_by(id=data.season_id, is_active=True).first()
        if season is None:
            raise HTTPException(status_code=404, detail="Season not found")
        if season.owner_id != user_id and not (user and user.is_admin):
            raise HTTPException(status_code=403, detail="Not the season owner")
    comp = crud.create_competition(db, data.model_dump())
    comp.owner_id = user_id
    db.commit()
    db.refresh(comp)
    return comp


@router.get("/{competition_id:int}")
def get_competition(competition_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    comp = crud.get_competition(db, competition_id)
    if not comp:
        raise HTTPException(status_code=404, detail="Competition not found.")
    return comp


@router.get("/list")
def list_competitions(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    rows = crud.list_competitions(db)
    return [{**{column.name: getattr(row, column.name) for column in row.__table__.columns},
             "registered_count": db.query(CompetitionRegistration).filter_by(competition_id=row.id).count(),
             "registered": db.query(CompetitionRegistration).filter_by(competition_id=row.id, user_id=user_id).first() is not None}
            for row in rows]


@router.put("/{competition_id}/update")
def update_competition(competition_id: int, data: CompetitionUpdate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    comp = crud.get_competition(db, competition_id)
    if not comp:
        raise HTTPException(status_code=404, detail="Competition not found")
    user = db.query(User).filter_by(id=user_id).first()
    if comp.owner_id != user_id and not (user and user.is_admin):
        raise HTTPException(status_code=403, detail="Not the competition owner")
    try:
        allowed = {key: value for key, value in data.updates.items() if key in {"name", "description", "sport", "level", "is_virtual"}}
        return crud.update_competition(db, competition_id, allowed)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{competition_id}/deactivate")
def deactivate_competition(competition_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    comp = crud.get_competition(db, competition_id)
    if not comp:
        raise HTTPException(status_code=404, detail="Competition not found")
    user = db.query(User).filter_by(id=user_id).first()
    if comp.owner_id != user_id and not (user and user.is_admin):
        raise HTTPException(status_code=403, detail="Not the competition owner")
    try:
        return crud.deactivate_competition(db, competition_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{competition_id}/register")
def register_for_competition(competition_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    comp = crud.get_competition(db, competition_id)
    if not comp or not comp.is_active:
        raise HTTPException(status_code=404, detail="Competition not found")
    row = db.query(CompetitionRegistration).filter_by(competition_id=competition_id, user_id=user_id).first()
    if row is None:
        row = CompetitionRegistration(competition_id=competition_id, user_id=user_id)
        db.add(row)
        db.commit()
    return {"competition_id": competition_id, "registered": True}


@router.delete("/{competition_id}/register")
def withdraw_from_competition(competition_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    row = db.query(CompetitionRegistration).filter_by(competition_id=competition_id, user_id=user_id).first()
    if row:
        db.delete(row)
        db.commit()
    return {"competition_id": competition_id, "registered": False}
