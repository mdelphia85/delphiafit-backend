from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.mission_replay import MissionReplay, MissionStep, MissionAnnotation


class MissionReplayCRUD:
    def start_replay(self, db: Session, data: dict, user_id: int):
        replay = MissionReplay(
            user_id=user_id,
            mission_type=data["mission_type"],
            mission_id=data["mission_id"],
            score=0.0,
            completed=False,
            started_at=datetime.utcnow(),
        )
        db.add(replay)
        db.commit()
        db.refresh(replay)
        return replay

    def list_replays(self, db: Session, user_id: int):
        return db.query(MissionReplay).filter(MissionReplay.user_id == user_id).order_by(MissionReplay.started_at.desc()).all()

    def get_owned_replay(self, db: Session, replay_id: int, user_id: int):
        replay = db.query(MissionReplay).filter(
            MissionReplay.id == replay_id,
            MissionReplay.user_id == user_id,
        ).first()
        if replay is None:
            raise HTTPException(status_code=404, detail="Replay not found.")
        return replay

    def complete_replay(self, db: Session, replay_id: int, user_id: int, score: float):
        replay = self.get_owned_replay(db, replay_id, user_id)
        replay.completed = True
        replay.score = score
        replay.ended_at = datetime.utcnow()
        db.commit()
        db.refresh(replay)
        return replay

    def add_step(self, db: Session, data: dict, user_id: int):
        self.get_owned_replay(db, data["replay_id"], user_id)
        step = MissionStep(
            replay_id=data["replay_id"],
            action_type=data["action_type"],
            description=data.get("description"),
            score_delta=data.get("score_delta", 0.0),
            timestamp=datetime.utcnow(),
        )
        db.add(step)
        db.commit()
        db.refresh(step)
        return step

    def list_steps(self, db: Session, replay_id: int, user_id: int):
        self.get_owned_replay(db, replay_id, user_id)
        return db.query(MissionStep).filter(MissionStep.replay_id == replay_id).all()

    def add_annotation(self, db: Session, data: dict, user_id: int):
        self.get_owned_replay(db, data["replay_id"], user_id)
        annotation = MissionAnnotation(
            replay_id=data["replay_id"],
            instructor_id=user_id,
            category=data["category"],
            note=data["note"],
            timestamp=datetime.utcnow(),
        )
        db.add(annotation)
        db.commit()
        db.refresh(annotation)
        return annotation

    def list_annotations(self, db: Session, replay_id: int, user_id: int):
        self.get_owned_replay(db, replay_id, user_id)
        return db.query(MissionAnnotation).filter(MissionAnnotation.replay_id == replay_id).all()
