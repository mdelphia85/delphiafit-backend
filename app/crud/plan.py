from sqlalchemy.orm import Session
from datetime import datetime

from app.models.plan import Plan
from app.models.client import Client
from app.models.team import Team


class PlanCRUD:

    # ---------------------------------------------------------
    # Create Plan
    # ---------------------------------------------------------
    def create_plan(self, db: Session, coach_id: int, name: str, description: str = None,
                    plan_type: str = "workout", content: str = None,
                    client_id: int = None, team_id: int = None):

        plan = Plan(
            coach_id=coach_id,
            client_id=client_id,
            team_id=team_id,
            name=name,
            description=description,
            plan_type=plan_type,
            content=content,
            version=1,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(plan)
        db.commit()
        db.refresh(plan)
        return plan

    # ---------------------------------------------------------
    # Get Plan by ID
    # ---------------------------------------------------------
    def get_plan(self, db: Session, plan_id: int):
        return db.query(Plan).filter(Plan.id == plan_id).first()

    # ---------------------------------------------------------
    # List Plans for Coach
    # ---------------------------------------------------------
    def list_plans_for_coach(self, db: Session, coach_id: int):
        return db.query(Plan).filter(Plan.coach_id == coach_id, Plan.is_active == True).all()

    # ---------------------------------------------------------
    # List Plans for Client
    # ---------------------------------------------------------
    def list_plans_for_client(self, db: Session, client_id: int):
        return db.query(Plan).filter(Plan.client_id == client_id, Plan.is_active == True).all()

    # ---------------------------------------------------------
    # List Plans for Team
    # ---------------------------------------------------------
    def list_plans_for_team(self, db: Session, team_id: int):
        return db.query(Plan).filter(Plan.team_id == team_id, Plan.is_active == True).all()

    # ---------------------------------------------------------
    # Update Plan
    # ---------------------------------------------------------
    def update_plan(self, db: Session, plan_id: int, updates: dict):
        plan = self.get_plan(db, plan_id)
        if not plan:
            raise ValueError("Plan not found.")

        for key, value in updates.items():
            if hasattr(plan, key):
                setattr(plan, key, value)

        plan.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(plan)
        return plan

    # ---------------------------------------------------------
    # Version Up Plan
    # ---------------------------------------------------------
    def version_up(self, db: Session, plan_id: int, new_content: str):
        plan = self.get_plan(db, plan_id)
        if not plan:
            raise ValueError("Plan not found.")

        plan.version += 1
        plan.content = new_content
        plan.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(plan)
        return plan

    # ---------------------------------------------------------
    # Assign Plan to Client
    # ---------------------------------------------------------
    def assign_plan_to_client(self, db: Session, plan_id: int, client_id: int):
        plan = self.get_plan(db, plan_id)
        client = db.query(Client).filter(Client.id == client_id).first()

        if not plan:
            raise ValueError("Plan not found.")
        if not client:
            raise ValueError("Client not found.")

        plan.client_id = client_id
        plan.team_id = None  # remove team assignment if switching
        plan.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(plan)
        return plan

    # ---------------------------------------------------------
    # Assign Plan to Team
    # ---------------------------------------------------------
    def assign_plan_to_team(self, db: Session, plan_id: int, team_id: int):
        plan = self.get_plan(db, plan_id)
        team = db.query(Team).filter(Team.id == team_id).first()

        if not plan:
            raise ValueError("Plan not found.")
        if not team:
            raise ValueError("Team not found.")

        plan.team_id = team_id
        plan.client_id = None  # remove client assignment if switching
        plan.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(plan)
        return plan

    # ---------------------------------------------------------
    # Deactivate Plan
    # ---------------------------------------------------------
    def deactivate_plan(self, db: Session, plan_id: int):
        plan = self.get_plan(db, plan_id)
        if not plan:
            raise ValueError("Plan not found.")

        plan.is_active = False
        plan.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(plan)
        return plan
