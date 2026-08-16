from sqlalchemy.orm import Session
from datetime import datetime

from app.models.swat import SWATPipeline, SWATDrill, SWATOperator, SWATEvaluation


class SWATCRUD:

    # ---------------------------------------------------------
    # Pipelines
    # ---------------------------------------------------------
    def create_pipeline(self, db: Session, data: dict):
        pipeline = SWATPipeline(
            name=data["name"],
            agency=data["agency"],
            description=data.get("description"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(pipeline)
        db.commit()
        db.refresh(pipeline)
        return pipeline

    def list_pipelines(self, db: Session):
        return db.query(SWATPipeline).filter(SWATPipeline.active == True).all()

    # ---------------------------------------------------------
    # Drills
    # ---------------------------------------------------------
    def add_drill(self, db: Session, data: dict):
        drill = SWATDrill(
            pipeline_id=data["pipeline_id"],
            name=data["name"],
            drill_type=data["drill_type"],
            standard=data.get("standard"),
            description=data.get("description")
        )
        db.add(drill)
        db.commit()
        db.refresh(drill)
        return drill

    def list_drills(self, db: Session, pipeline_id: int):
        return db.query(SWATDrill).filter(
            SWATDrill.pipeline_id == pipeline_id
        ).all()

    # ---------------------------------------------------------
    # Operators
    # ---------------------------------------------------------
    def add_operator(self, db: Session, data: dict):
        operator = SWATOperator(
            user_id=data["user_id"],
            pipeline_id=data["pipeline_id"],
            status="active"
        )
        db.add(operator)
        db.commit()
        db.refresh(operator)
        return operator

    def list_operators(self, db: Session, pipeline_id: int):
        return db.query(SWATOperator).filter(
            SWATOperator.pipeline_id == pipeline_id
        ).all()

    # ---------------------------------------------------------
    # Evaluations
    # ---------------------------------------------------------
    def evaluate(self, db: Session, data: dict):
        evaluation = SWATEvaluation(
            operator_id=data["operator_id"],
            drill_id=data["drill_id"],
            score=data.get("score"),
            passed=data.get("passed", False),
            notes=data.get("notes"),
            timestamp=datetime.utcnow()
        )
        db.add(evaluation)
        db.commit()
        db.refresh(evaluation)
        return evaluation

    def get_evaluations(self, db: Session, operator_id: int):
        return db.query(SWATEvaluation).filter(
            SWATEvaluation.operator_id == operator_id
        ).all()
