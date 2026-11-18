from sqlalchemy.orm import Session
from datetime import datetime

from app.models.team import Team
from app.models.client import Client
from app.models.schedule import Schedule
from app.models.recruit import Recruit
from app.models.invite import Invite


class TeamCRUD:

    # ---------------------------------------------------------
    # Create Team
    # ---------------------------------------------------------
    def create_team(self, db: Session, coach_id: int, name: str, sport: str = None,
                    level: str = None, organization: str = None, season: str = None):

        team = Team(
            coach_id=coach_id,
            name=name,
            sport=sport,
            level=level,
            organization=organization,
            season=season,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(team)
        db.commit()
        db.refresh(team)
        return team

    # ---------------------------------------------------------
    # Get Team by ID
    # ---------------------------------------------------------
    def get_team(self, db: Session, team_id: int):
        return db.query(Team).filter(Team.id == team_id).first()

    # ---------------------------------------------------------
    # List Teams for Coach
    # ---------------------------------------------------------
    def list_teams_for_coach(self, db: Session, coach_id: int):
        return db.query(Team).filter(Team.coach_id == coach_id, Team.is_active == True).all()

    # ---------------------------------------------------------
    # Update Team
    # ---------------------------------------------------------
    def update_team(self, db: Session, team_id: int, updates: dict):
        team = self.get_team(db, team_id)
        if not team:
            raise ValueError("Team not found.")

        for key, value in updates.items():
            if hasattr(team, key):
                setattr(team, key, value)

        team.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(team)
        return team

    # ---------------------------------------------------------
    # Deactivate Team
    # ---------------------------------------------------------
    def deactivate_team(self, db: Session, team_id: int):
        team = self.get_team(db, team_id)
        if not team:
            raise ValueError("Team not found.")

        team.is_active = False
        team.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(team)
        return team

    # ---------------------------------------------------------
    # Add Client to Team
    # ---------------------------------------------------------
    def add_client_to_team(self, db: Session, team_id: int, client_id: int):
        team = self.get_team(db, team_id)
        client = db.query(Client).filter(Client.id == client_id).first()

        if not team:
            raise ValueError("Team not found.")
        if not client:
            raise ValueError("Client not found.")

        client.team_id = team_id
        client.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(client)
        return client

    # ---------------------------------------------------------
    # Remove Client from Team
    # ---------------------------------------------------------
    def remove_client_from_team(self, db: Session, team_id: int, client_id: int):
        client = db.query(Client).filter(Client.id == client_id).first()

        if not client:
            raise ValueError("Client not found.")
        if client.team_id != team_id:
            raise ValueError("Client is not on this team.")

        client.team_id = None
        client.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(client)
        return client

    # ---------------------------------------------------------
    # Get Team Roster
    # ---------------------------------------------------------
    def get_team_roster(self, db: Session, team_id: int):
        return db.query(Client).filter(Client.team_id == team_id).all()

    # ---------------------------------------------------------
    # Get Team Schedules
    # ---------------------------------------------------------
    def get_team_schedules(self, db: Session, team_id: int):
        return db.query(Schedule).filter(Schedule.team_id == team_id).all()

    # ---------------------------------------------------------
    # Get Team Recruits
    # ---------------------------------------------------------
    def get_team_recruits(self, db: Session, team_id: int):
        return db.query(Recruit).filter(Recruit.team_id == team_id).all()

    # ---------------------------------------------------------
    # Get Team Invites
    # ---------------------------------------------------------
    def get_team_invites(self, db: Session, team_id: int):
        return db.query(Invite).filter(Invite.team_id == team_id).all()
