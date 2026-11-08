from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from app.models.coach import Coach
from app.models.invite import Invite
from app.models.team import Team
from app.models.client import Client


class CoachCRUD:

    # ---------------------------------------------------------
    # Create Coach
    # ---------------------------------------------------------
    def create_coach(self, db: Session, email: str, name: str, organization: str = None, role: str = "coach"):
        coach = Coach(
            email=email,
            name=name,
            organization=organization,
            role=role,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        try:
            db.add(coach)
            db.commit()
            db.refresh(coach)
            return coach
        except IntegrityError:
            db.rollback()
            raise ValueError("A coach with this email already exists.")

    # ---------------------------------------------------------
    # Get Coach by ID
    # ---------------------------------------------------------
    def get_coach(self, db: Session, coach_id: int):
        return db.query(Coach).filter(Coach.id == coach_id).first()

    # ---------------------------------------------------------
    # Get Coach by Email (login)
    # ---------------------------------------------------------
    def get_coach_by_email(self, db: Session, email: str):
        return db.query(Coach).filter(Coach.email == email).first()

    # ---------------------------------------------------------
    # List All Coaches
    # ---------------------------------------------------------
    def list_coaches(self, db: Session):
        return db.query(Coach).filter(Coach.is_active == True).all()

    # ---------------------------------------------------------
    # Update Coach
    # ---------------------------------------------------------
    def update_coach(self, db: Session, coach_id: int, updates: dict):
        coach = (
            db.query(Coach)
            .filter(Coach.id == coach_id)
            .with_for_update()
            .populate_existing()
            .first()
        )
        if not coach:
            raise ValueError("Coach not found.")

        try:
            revoke_sessions = False
            for key, value in updates.items():
                if key == "token_version":
                    continue
                if hasattr(coach, key):
                    if key == "hashed_password" and value != coach.hashed_password:
                        revoke_sessions = True
                    elif key == "is_active" and value != coach.is_active:
                        revoke_sessions = True
                    setattr(coach, key, value)

            if revoke_sessions:
                coach.token_version = Coach.token_version + 1
            coach.updated_at = datetime.utcnow()
            db.commit()
        except Exception:
            db.rollback()
            raise
        db.refresh(coach)
        return coach

    # ---------------------------------------------------------
    # Deactivate Coach
    # ---------------------------------------------------------
    def deactivate_coach(self, db: Session, coach_id: int):
        coach = (
            db.query(Coach)
            .filter(Coach.id == coach_id)
            .with_for_update()
            .populate_existing()
            .first()
        )
        if not coach:
            raise ValueError("Coach not found.")

        try:
            if coach.is_active:
                coach.is_active = False
                coach.token_version = Coach.token_version + 1
            coach.updated_at = datetime.utcnow()
            db.commit()
        except Exception:
            db.rollback()
            raise
        db.refresh(coach)
        return coach

    # ---------------------------------------------------------
    # Legacy client invitation acceptance
    # ---------------------------------------------------------
    def accept_invite(self, db: Session, token: str, name: str):
        invite = db.query(Invite).filter(Invite.token == token).with_for_update().first()
        if not invite:
            raise ValueError("Invalid invite token.")

        if invite.role != "client":
            raise ValueError("Coach invitations must be accepted through the authenticated coach invitation flow.")

        if invite.accepted:
            raise ValueError("Invite already accepted.")

        if invite.expires_at and invite.expires_at < datetime.utcnow():
            raise ValueError("Invite has expired.")

        invite.accepted = True
        invite.accepted_at = datetime.utcnow()

        # Role determines what gets created
        if invite.role == "client":
            client = Client(
                coach_id=invite.coach_id,
                team_id=invite.team_id,
                email=invite.email,
                name=name,
                status="active",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(client)

        db.commit()
        return {"message": "Invite accepted successfully."}

    # ---------------------------------------------------------
    # Get Coach Teams
    # ---------------------------------------------------------
    def get_coach_teams(self, db: Session, coach_id: int):
        coach = self.get_coach(db, coach_id)
        if not coach:
            raise ValueError("Coach not found.")
        return coach.teams

    # ---------------------------------------------------------
    # Get Coach Clients
    # ---------------------------------------------------------
    def get_coach_clients(self, db: Session, coach_id: int):
        coach = self.get_coach(db, coach_id)
        if not coach:
            raise ValueError("Coach not found.")
        return coach.clients
