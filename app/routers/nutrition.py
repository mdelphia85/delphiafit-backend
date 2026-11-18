"""Authenticated nutrition logging with durable, per-user write deduplication."""
import hashlib
import json
import re

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database.connection import get_db
from app.utils.security import get_current_user_id
from app.models.user import User
from app.models.nutrition import NutritionLog
from app.models.user_data_record import UserDataRecord
from app.schemas.nutrition import NutritionLogCreate, NutritionLogRead
from app.crud.nutrition import create_nutrition_log, get_nutrition_logs

router = APIRouter(prefix="/nutrition", tags=["nutrition"])
_DEDUPE_COLLECTION = "nutrition_write_requests"
_KEY_FORMAT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$")


def _create_idempotently(db: Session, user_id: int, payload: NutritionLogCreate, key: str):
    # Explicit keys only. This is not meant to deduplicate separate meals
    # that happen to have identical macros.
    if not _KEY_FORMAT.fullmatch(key):
        raise HTTPException(status_code=422, detail="Invalid Idempotency-Key.")

    fingerprint = hashlib.sha256(
        json.dumps(payload.model_dump(), sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    # Serialize requests from one account before examining dedupe markers;
    # PostgreSQL holds this row lock until the transaction commits.
    owner = db.query(User.id).filter(User.id == user_id).with_for_update().one_or_none()
    if owner is None:
        raise HTTPException(status_code=401, detail="Invalid user token.")

    markers = db.query(UserDataRecord).filter_by(
        user_id=user_id, collection=_DEDUPE_COLLECTION
    ).all()
    existing = next((row for row in markers if row.data.get("key") == key), None)
    if existing is not None:
        if existing.data.get("fingerprint") != fingerprint:
            raise HTTPException(status_code=409, detail="Idempotency key was used for different nutrition details.")
        log = db.query(NutritionLog).filter_by(
            user_id=user_id, id=existing.data.get("nutrition_id")
        ).one_or_none()
        if log is None:
            raise HTTPException(status_code=409, detail="The original nutrition record is no longer available.")
        return log

    log = NutritionLog(
        user_id=user_id,
        calories=payload.calories,
        protein=payload.protein,
        carbs=payload.carbs,
        fats=payload.fats,
        water_oz=payload.water_oz,
        notes=payload.notes,
    )
    db.add(log)
    db.flush()
    db.add(UserDataRecord(
        user_id=user_id, collection=_DEDUPE_COLLECTION,
        data={"key": key, "fingerprint": fingerprint, "nutrition_id": log.id}
    ))
    # Log and marker are committed together, or rolled back together.
    db.commit()
    db.refresh(log)
    return log


@router.post("/", response_model=NutritionLogRead)
def add_nutrition_log(
    payload: NutritionLogCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    if idempotency_key is None:
        # Preserve legacy manual logging behavior until every client adopts keys.
        return create_nutrition_log(db, user_id, payload)
    return _create_idempotently(db, user_id, payload, idempotency_key)


@router.get("/", response_model=List[NutritionLogRead])
def list_nutrition_logs(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    return get_nutrition_logs(db, user_id)
