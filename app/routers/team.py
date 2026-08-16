from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.database import get_db
from app.crud.team import TeamCRUD

router = APIRouter(prefix="/team", tags=["Team"])
team_crud = TeamCRUD()


# ---------------------------------------------------------
# Request Models
# ---------------------------------------------------------

class TeamCreate(BaseModel):
    coach_id: int
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
# Create Team
# ---------------------------------------------------------
@router.post("/create")
def create_team(data: TeamCreate, db: Session = Depends(get_db)):
    try:
        return team_crud.create_team(
            db=db,
            coach_id=data.coach_id,
            name=data.name,
            sport=data.sport,
            level=data.level,
            organization=data.organization,
            season=data.season
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Get Team by ID
# ---------------------------------------------------------
@router.get("/{team_id}")
def get_team(team_id: int, db: Session = Depends(get_db)):
    team = team_crud.get_team(db, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found.")
    return team


# ---------------------------------------------------------
# List Teams for Coach
# ---------------------------------------------------------
@router.get("/coach/{coach_id}")
def list_teams_for_coach(coach_id: int, db: Session = Depends(get_db)):
    return team_crud.list_teams_for_coach(db, coach_id)


# ---------------------------------------------------------
# Update Team
# ---------------------------------------------------------
@router.put("/{team_id}/update")
def update_team(team_id: int, data: TeamUpdate, db: Session = Depends(get_db)):
    try:
        return team_crud.update_team(db, team_id, data.updates)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Deactivate Team
# ---------------------------------------------------------
@router.delete("/{team_id}/deactivate")
def deactivate_team(team_id: int, db: Session = Depends(get_db)):
    try:
        return team_crud.deactivate_team(db, team_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Add Client to Team
# ---------------------------------------------------------
@router.post("/{team_id}/add-client")
def add_client_to_team(team_id: int, data: ClientAssignment, db: Session = Depends(get_db)):
    try:
        return team_crud.add_client_to_team(db, team_id, data.client_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Remove Client from Team
# ---------------------------------------------------------
@router.post("/{team_id}/remove-client")
def remove_client_from_team(team_id: int, data: ClientAssignment, db: Session = Depends(get_db)):
    try:
        return team_crud.remove_client_from_team(db, team_id, data.client_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Get Team Roster
# ---------------------------------------------------------
@router.get("/{team_id}/roster")
def get_team_roster(team_id: int, db: Session = Depends(get_db)):
    return team_crud.get_team_roster(db, team_id)


# ---------------------------------------------------------
# Get Team Schedules
# ---------------------------------------------------------
@router.get("/{team_id}/schedules")
def get_team_schedules(team_id: int, db: Session = Depends(get_db)):
    return team_crud.get_team_schedules(db, team_id)


# ---------------------------------------------------------
# Get Team Recruits
# ---------------------------------------------------------
@router.get("/{team_id}/recruits")
def get_team_recruits(team_id: int, db: Session = Depends(get_db)):
    return team_crud.get_team_recruits(db, team_id)


# ---------------------------------------------------------
# Get Team Invites
# ---------------------------------------------------------
@router.get("/{team_id}/invites")
def get_team_invites(team_id: int, db: Session = Depends(get_db)):
    return team_crud.get_team_invites(db, team_id)
