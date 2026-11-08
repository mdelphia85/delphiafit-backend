from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.progress_snapshot import ProgressSnapshot
from app.schemas.progress_snapshot import ProgressSnapshotCreate, ProgressSnapshotUpdate


def create_progress_snapshot(db: Session, user_id: int, data: ProgressSnapshotCreate) -> ProgressSnapshot:
    snapshot = ProgressSnapshot(user_id=user_id, metric=data.metric, value=data.value)
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def get_progress_snapshot(db: Session, snapshot_id: int) -> Optional[ProgressSnapshot]:
    return db.query(ProgressSnapshot).filter(ProgressSnapshot.id == snapshot_id).first()


def get_progress_snapshots(db: Session, user_id: int) -> List[ProgressSnapshot]:
    return db.query(ProgressSnapshot).filter(ProgressSnapshot.user_id == user_id).order_by(ProgressSnapshot.recorded_at.desc()).all()


def update_progress_snapshot(db: Session, snapshot_id: int, data: ProgressSnapshotUpdate) -> Optional[ProgressSnapshot]:
    snapshot = get_progress_snapshot(db, snapshot_id)
    if not snapshot:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(snapshot, field, value)
    db.commit(); db.refresh(snapshot); return snapshot


def delete_progress_snapshot(db: Session, snapshot_id: int) -> bool:
    snapshot = get_progress_snapshot(db, snapshot_id)
    if not snapshot: return False
    db.delete(snapshot); db.commit(); return True
