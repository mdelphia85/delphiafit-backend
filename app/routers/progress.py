from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database.connection import get_db
from app.utils.security import get_current_user_id

# Schemas
from app.schemas.strength_metric import StrengthMetricCreate, StrengthMetricRead
from app.schemas.pr_records import PersonalRecordCreate, PersonalRecordRead
from app.schemas.progress_snapshot import ProgressSnapshotCreate, ProgressSnapshotRead
from app.schemas.recovery import RecoveryCreate, RecoveryRead
from app.schemas.periodization import PeriodizationBlockCreate, PeriodizationBlockRead

# CRUD
from app.crud.strength_metric import create_strength_metric, get_strength_metrics
from app.crud.pr_records import create_pr, get_prs
from app.crud.progress_snapshot import create_progress_snapshot, get_progress_snapshots
from app.crud.recovery import create_recovery_log, get_recovery_logs
from app.crud.periodization import create_periodization_block, get_periodization_blocks

router = APIRouter(prefix="/progress", tags=["progress"])

# ---------------------------
# Strength Metrics
# ---------------------------

@router.post("/strength", response_model=StrengthMetricRead)
def add_strength_metric(
    payload: StrengthMetricCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return create_strength_metric(db, user_id, payload)

@router.get("/strength", response_model=List[StrengthMetricRead])
def list_strength_metrics(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return get_strength_metrics(db, user_id)


# ---------------------------
# Personal Records (PRs)
# ---------------------------

@router.post("/prs", response_model=PersonalRecordRead)
def add_pr(
    payload: PersonalRecordCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return create_pr(db, user_id, payload)

@router.get("/prs", response_model=List[PersonalRecordRead])
def list_prs(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return get_prs(db, user_id)


# ---------------------------
# Progress Snapshots
# ---------------------------

@router.post("/snapshots", response_model=ProgressSnapshotRead)
def add_progress_snapshot(
    payload: ProgressSnapshotCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return create_progress_snapshot(db, user_id, payload)

@router.get("/snapshots", response_model=List[ProgressSnapshotRead])
def list_progress_snapshots(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return get_progress_snapshots(db, user_id)


# ---------------------------
# Recovery Logs
# ---------------------------

@router.post("/recovery", response_model=RecoveryRead)
def add_recovery_log(
    payload: RecoveryCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return create_recovery_log(db, user_id, payload)

@router.get("/recovery", response_model=List[RecoveryRead])
def list_recovery_logs(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return get_recovery_logs(db, user_id)


# ---------------------------
# Periodization Blocks
# ---------------------------

@router.post("/periodization", response_model=PeriodizationBlockRead)
def add_periodization_block(
    payload: PeriodizationBlockCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return create_periodization_block(db, user_id, payload)

@router.get("/periodization", response_model=List[PeriodizationBlockRead])
def list_periodization_blocks(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return get_periodization_blocks(db, user_id)
