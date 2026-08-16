from sqlalchemy.orm import Session
from app.models.progress_snapshot import ProgressSnapshot
from app.schemas.progress_snapshot import ProgressSnapshotCreate

def create_progress_snapshot(db: Session, user_id: int, data: ProgressSnapshotCreate):
    snapshot = ProgressSnapshot(
        user_id=user_id,
        metric=data.metric,
        value=data.value
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot

def get_progress_snapshots(db: Session, user_id: int):
    return db.query(ProgressSnapshot).filter(ProgressSnapshot.user_id == user_id).all()
