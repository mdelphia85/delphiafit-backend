from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.coach_dependencies import get_current_coach
from app.crud.team import TeamCRUD
from app.database.connection import get_db
from app.models.client import Client
from app.models.coach import Coach
from app.services.coach_access import get_accessible_team, get_managed_client

router = APIRouter(prefix="/team", tags=["Team"])
team_crud = TeamCRUD()

# Fields a coach may change through the generic update route.
UPDATABLE_TEAM_FIELDS = {"name", "sport", "level", "organization", "season"}


# ---------------------------------------------------------
# Request Models
# ---------------------------------------------------------

class TeamCreate(BaseModel):
    coach_id: Optional[int] = None  # ignored; the team is always owned by the caller
    name: str
    sport: Optional[str] = None
    level: Optional[str] = None
    organization: Optional[str] = None
    season: Optional[str] = None


class TeamUpdate(BaseModel):
    updates: Dict[str, Any]


class ClientAssignment(BaseModel):
    client_id: int


# ---------------------------------------------------------
# Every route requires a coach token and checks team access.
# ---------------------------------------------------------
@router.post("/create")
def create_team(data: TeamCreate, coach: Coach = Depends(get_current_coach), db: Session = Depends(get_db)):
    if data.coach_id is not None and data.coach_id != coach.id:
        raise HTTPException(status_code=403, detail="You can only create teams for yourself")
    try:
        return team_crud.create_team(
            db=db,
            coach_id=coach.id,
            name=data.name,
            sport=data.sport,
            level=data.level,
            organization=data.organization,
            season=data.season,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/coach/{coach_id}")
def list_teams_for_coach(coach_id: int, coach: Coach = Depends(get_current_coach), db: Session = Depends(get_db)):
    if coach_id != coach.id:
        raise HTTPException(status_code=403, detail="You can only list your own teams")
    return team_crud.list_teams_for_coach(db, coach_id)


@router.get("/{team_id}")
def get_team(team_id: int, coach: Coach = Depends(get_current_coach), db: Session = Depends(get_db)):
    return get_accessible_team(db, coach, team_id)


@router.put("/{team_id}/update")
def update_team(team_id: int, data: TeamUpdate, coach: Coach = Depends(get_current_coach), db: Session = Depends(get_db)):
    get_accessible_team(db, coach, team_id, owner_only=True)
    updates = {key: value for key, value in data.updates.items() if key in UPDATABLE_TEAM_FIELDS}
    try:
        return team_crud.update_team(db, team_id, updates)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{team_id}/deactivate")
def deactivate_team(team_id: int, coach: Coach = Depends(get_current_coach), db: Session = Depends(get_db)):
    get_accessible_team(db, coach, team_id, owner_only=True)
    try:
        return team_crud.deactivate_team(db, team_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{team_id}/add-client")
def add_client_to_team(
    team_id: int, data: ClientAssignment, coach: Coach = Depends(get_current_coach), db: Session = Depends(get_db)
):
    get_accessible_team(db, coach, team_id)
    get_managed_client(db, coach, data.client_id)
    try:
        return team_crud.add_client_to_team(db, team_id, data.client_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{team_id}/remove-client")
def remove_client_from_team(
    team_id: int, data: ClientAssignment, coach: Coach = Depends(get_current_coach), db: Session = Depends(get_db)
):
    get_accessible_team(db, coach, team_id)
    get_managed_client(db, coach, data.client_id)
    try:
        return team_crud.remove_client_from_team(db, team_id, data.client_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{team_id}/roster")
def get_team_roster(team_id: int, coach: Coach = Depends(get_current_coach), db: Session = Depends(get_db)):
    get_accessible_team(db, coach, team_id)
    return team_crud.get_team_roster(db, team_id)


@router.get("/{team_id}/schedules")
def get_team_schedules(team_id: int, coach: Coach = Depends(get_current_coach), db: Session = Depends(get_db)):
    get_accessible_team(db, coach, team_id)
    return team_crud.get_team_schedules(db, team_id)


@router.get("/{team_id}/recruits")
def get_team_recruits(team_id: int, coach: Coach = Depends(get_current_coach), db: Session = Depends(get_db)):
    get_accessible_team(db, coach, team_id)
    return team_crud.get_team_recruits(db, team_id)


@router.get("/{team_id}/invites")
def get_team_invites(team_id: int, coach: Coach = Depends(get_current_coach), db: Session = Depends(get_db)):
    get_accessible_team(db, coach, team_id)
    return team_crud.get_team_invites(db, team_id)
