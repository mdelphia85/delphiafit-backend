from sqlalchemy.orm import Session
from datetime import datetime

from app.models.drill import Drill
from app.models.plan import Plan


class DrillCRUD:

    # ---------------------------------------------------------
    # Create Drill
    # ---------------------------------------------------------
    def create_drill(self, db: Session, coach_id: int, name: str, category: str = None,
                     tags: str = None, difficulty: str = "medium", equipment: str = None,
                     video_url: str = None, image_url: str = None, instructions: str = None):

        drill = Drill(
            coach_id=coach_id,
            name=name,
            category=category,
            tags=tags,
            difficulty=difficulty,
            equipment=equipment,
            video_url=video_url,
            image_url=image_url,
            instructions=instructions,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(drill)
        db.commit()
        db.refresh(drill)
        return drill

    # ---------------------------------------------------------
    # Get Drill by ID
    # ---------------------------------------------------------
    def get_drill(self, db: Session, drill_id: int):
        return db.query(Drill).filter(Drill.id == drill_id).first()

    # ---------------------------------------------------------
    # List Drills for Coach
    # ---------------------------------------------------------
    def list_drills_for_coach(self, db: Session, coach_id: int):
        return db.query(Drill).filter(Drill.coach_id == coach_id, Drill.is_active == True).all()

    # ---------------------------------------------------------
    # Search Drills by Category
    # ---------------------------------------------------------
    def search_by_category(self, db: Session, coach_id: int, category: str):
        return db.query(Drill).filter(
            Drill.coach_id == coach_id,
            Drill.category == category,
            Drill.is_active == True
        ).all()

    # ---------------------------------------------------------
    # Search Drills by Tag
    # ---------------------------------------------------------
    def search_by_tag(self, db: Session, coach_id: int, tag: str):
        return db.query(Drill).filter(
            Drill.coach_id == coach_id,
            Drill.tags.like(f"%{tag}%"),
            Drill.is_active == True
        ).all()

    # ---------------------------------------------------------
    # Update Drill
    # ---------------------------------------------------------
    def update_drill(self, db: Session, drill_id: int, updates: dict):
        drill = self.get_drill(db, drill_id)
        if not drill:
            raise ValueError("Drill not found.")

        for key, value in updates.items():
            if hasattr(drill, key):
                setattr(drill, key, value)

        drill.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(drill)
        return drill

    # ---------------------------------------------------------
    # Deactivate Drill
    # ---------------------------------------------------------
    def deactivate_drill(self, db: Session, drill_id: int):
        drill = self.get_drill(db, drill_id)
        if not drill:
            raise ValueError("Drill not found.")

        drill.is_active = False
        drill.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(drill)
        return drill

    # ---------------------------------------------------------
    # Attach Drill to Plan (optional helper)
    # ---------------------------------------------------------
    def attach_drill_to_plan(self, db: Session, plan_id: int, drill_id: int):
        plan = db.query(Plan).filter(Plan.id == plan_id).first()
        drill = self.get_drill(db, drill_id)

        if not plan:
            raise ValueError("Plan not found.")
        if not drill:
            raise ValueError("Drill not found.")

        # Append drill reference into plan content JSON-like text
        # Frontend will parse this structure
        import json

        content = plan.content or "{}"
        try:
            content_json = json.loads(content)
        except:
            content_json = {}

        if "drills" not in content_json:
            content_json["drills"] = []

        content_json["drills"].append({
            "drill_id": drill.id,
            "name": drill.name,
            "category": drill.category,
            "difficulty": drill.difficulty
        })

        plan.content = json.dumps(content_json)
        plan.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(plan)
        return plan
