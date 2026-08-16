from sqlalchemy.orm import Session
from datetime import datetime

from app.models.mission_replay import MissionReplay, MissionStep, MissionAnnotation


class MissionReplayCRUD:

    # ---------------------------------------------------------
    # Replay
    # ---------------------------------------------------------
    def start_replay(self, db: Session, data: dict):
        replay = MissionReplay(
            user_id=data["user_id"],
            mission_type=data["mission_type"],
            mission_id=data["mission_id"],
            score=0.0,
            completed=False,
            started_at=datetime.utcnow()
        )
        db.add(replay)
        db.commit()
        db.refresh(replay)
        return replay

    def complete_replay(self, db: Session, replay_id: int, score: float):
        replay = db.query(MissionReplay).filter(MissionReplay.id == replay_id).first()
        replay.completed = True
        replay.score = score
        replay.ended_at = datetime.utcnow()
        db.commit()
        db.refresh(replay)
        return replay

    def get_replay(self, db: Session, replay_id: int):
        return db.query(MissionReplay).filter(MissionReplay.id == replay_id).first()

    # ---------------------------------------------------------
    # Steps
    # ---------------------------------------------------------
    def add_step(self, db: Session, data: dict):
        step = MissionStep(
            replay_id=data["replay_id"],
            action_type=data["action_type"],
            description=data.get("description"),
            score_delta=data.get("score_delta", 0.0),
            timestamp=datetime.utcnow()
        )
        db.add(step)
        db.commit()
        db.refresh(step)
        return step

    def list_steps(self, db: Session, replay_id: int):
        return db.query(MissionStep).filter(
            MissionStep.replay_id == replay_id
        ).all()

    # ---------------------------------------------------------
    # Annotations
    # ---------------------------------------------------------
    def add_annotation(self, db: Session, data: dict):
        annotation = MissionAnnotation(
            replay_id=data["replay_id"],
            instructor_id=data["instructor_id"],
            category=data["category"],
            note=data["note"],
            timestamp=datetime.utcnow()
        )
        db.add(annotation)
        db.commit()
        db.refresh(annotation)
        return annotation

    def list_annotations(self, db: Session, replay_id: int):
        return db.query(MissionAnnotation).filter(
            MissionAnnotation.replay_id == replay_id
        ).all()
