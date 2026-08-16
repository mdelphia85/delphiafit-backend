from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.progress_snapshot import ProgressSnapshot
from app.schemas.progress_snapshot import ProgressSnapshotCreate, ProgressSnapshotUpdate


def create_progress_snapshot(db: Session, data: ProgressSnapshotCreate) -> ProgressSnapshot:
    snapshot = ProgressSnapshot(
        user_id=data.user_id,
        weight=data.weight,
        body_fat=data.body_fat,
        notes=data.notes,
        timestamp=data.timestamp or datetime.utcnow(),
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def get_progress_snapshot(db: Session, snapshot_id: int) -> Optional[ProgressSnapshot]:
    return db.query(ProgressSnapshot).filter(ProgressSnapshot.id == snapshot_id).first()


def get_progress_snapshots_for_user(db: Session, user_id: int) -> List[ProgressSnapshot]:
    return (
        db.query(ProgressSnapshot)
        .filter(ProgressSnapshot.user_id == user_id)
        .order_by(ProgressSnapshot.timestamp.desc())
        .all()
    )


def update_progress_snapshot(db: Session, snapshot_id: int, data: ProgressSnapshotUpdate) -> Optional[ProgressSnapshot]:
    snapshot = get_progress_snapshot(db, snapshot_id)
    if not snapshot:
        return None

    for field, value in data.dict(exclude_unset=True).items():
        setattr(snapshot, field, value)

    db.commit()
    db.refresh(snapshot)
    return snapshot


def delete_progress_snapshot(db: Session, snapshot_id: int) -> bool:
    snapshot = get_progress_snapshot(db, snapshot_id)
    if not snapshot:
        return False

    db.delete(snapshot)
    db.commit()
    return True
