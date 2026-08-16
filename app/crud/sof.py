from sqlalchemy.orm import Session
from datetime import datetime

from app.models.sof import SOFPipeline, SOFEvent, SOFCandidate, SOFEvaluation


class SOFCRUD:

    # ---------------------------------------------------------
    # Pipelines
    # ---------------------------------------------------------
    def create_pipeline(self, db: Session, data: dict):
        pipeline = SOFPipeline(
            name=data["name"],
            branch=data["branch"],
            description=data.get("description"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(pipeline)
        db.commit()
        db.refresh(pipeline)
        return pipeline

    def list_pipelines(self, db: Session):
        return db.query(SOFPipeline).filter(SOFPipeline.active == True).all()

    # ---------------------------------------------------------
    # Events
    # ---------------------------------------------------------
    def add_event(self, db: Session, data: dict):
        event = SOFEvent(
            pipeline_id=data["pipeline_id"],
            name=data["name"],
            event_type=data["event_type"],
            standard=data.get("standard"),
            description=data.get("description")
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    def list_events(self, db: Session, pipeline_id: int):
        return db.query(SOFEvent).filter(
            SOFEvent.pipeline_id == pipeline_id
        ).all()

    # ---------------------------------------------------------
    # Candidates
    # ---------------------------------------------------------
    def add_candidate(self, db: Session, data: dict):
        candidate = SOFCandidate(
            user_id=data["user_id"],
            pipeline_id=data["pipeline_id"],
            status="active"
        )
        db.add(candidate)
        db.commit()
        db.refresh(candidate)
        return candidate

    def list_candidates(self, db: Session, pipeline_id: int):
        return db.query(SOFCandidate).filter(
            SOFCandidate.pipeline_id == pipeline_id
        ).all()

    # ---------------------------------------------------------
    # Evaluations
    # ---------------------------------------------------------
    def evaluate(self, db: Session, data: dict):
        evaluation = SOFEvaluation(
            candidate_id=data["candidate_id"],
            event_id=data["event_id"],
            score=data.get("score"),
            passed=data.get("passed", False),
            notes=data.get("notes"),
            timestamp=datetime.utcnow()
        )
        db.add(evaluation)
        db.commit()
        db.refresh(evaluation)
        return evaluation

    def get_evaluations(self, db: Session, candidate_id: int):
        return db.query(SOFEvaluation).filter(
            SOFEvaluation.candidate_id == candidate_id
        ).all()
