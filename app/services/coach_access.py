"""Ownership checks shared by the coach-facing routers."""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.coach import Coach
from app.models.coach_team_membership import CoachTeamMembership
from app.models.team import Team


def accessible_team_ids(db: Session, coach_id: int) -> list[int]:
    owned = [row[0] for row in db.query(Team.id).filter(Team.coach_id == coach_id, Team.is_active.is_(True)).all()]
    shared = [
        row[0]
        for row in db.query(CoachTeamMembership.team_id)
        .join(Team, Team.id == CoachTeamMembership.team_id)
        .filter(CoachTeamMembership.coach_id == coach_id, Team.is_active.is_(True))
        .all()
    ]
    return list(dict.fromkeys(owned + shared))


def get_accessible_team(db: Session, coach: Coach, team_id: int, owner_only: bool = False) -> Team:
    team = db.query(Team).filter(Team.id == team_id, Team.is_active.is_(True)).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if team.coach_id == coach.id:
        return team
    if owner_only or team.id not in accessible_team_ids(db, coach.id):
        raise HTTPException(status_code=403, detail="You do not have access to that team")
    return team


def get_managed_client(db: Session, coach: Coach, client_id: int, include_inactive: bool = False) -> Client:
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client or (client.status == "inactive" and not include_inactive):
        raise HTTPException(status_code=404, detail="Client not found")
    if client.coach_id != coach.id and (client.team_id is None or client.team_id not in accessible_team_ids(db, coach.id)):
        raise HTTPException(status_code=403, detail="You do not manage this client")
    return client


def managed_clients_query(db: Session, coach: Coach):
    team_ids = accessible_team_ids(db, coach.id)
    query = db.query(Client).filter(Client.status != "inactive")
    if team_ids:
        return query.filter((Client.coach_id == coach.id) | (Client.team_id.in_(team_ids)))
    return query.filter(Client.coach_id == coach.id)
