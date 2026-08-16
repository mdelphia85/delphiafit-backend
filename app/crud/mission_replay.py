from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.mission_replay import MissionReplay


def create_mission_replay(db: Session, data: dict) -> MissionReplay:
    replay = MissionReplay(**data)
    db.add(replay)
    db.commit()
    db.refresh(replay)
    return replay


def get_mission_replay(db: Session, replay_id: int) -> Optional[MissionReplay]:
    return db.query(MissionReplay).filter(MissionReplay.id == replay_id).first()


def get_mission_replays(db: Session) -> List[MissionReplay]:
    return db.query(MissionReplay).all()


def update_mission_replay(db: Session, replay_id: int, data: dict) -> Optional[MissionReplay]:
    replay = get_mission_replay(db, replay_id)
    if not replay:
        return None

    for field, value in data.items():
        setattr(replay, field, value)

    db.commit()
    db.refresh(replay)
    return replay


def delete_mission_replay(db: Session, replay_id: int) -> bool:
    replay = get_mission_replay(db, replay_id)
    if not replay:
        return False

    db.delete(replay)
    db.commit()
    return True
