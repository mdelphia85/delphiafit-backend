"""Authenticated barcode lookup and private scan history.

Scan history stores only user-submitted barcode numbers, never licensed product
details. Product metadata is fetched separately with full source attribution.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.user_data_record import UserDataRecord
from app.services.food_scan import (
    ScanProviderUnavailable,
    ScanRateLimited,
    get_product,
    valid_barcode,
)
from app.utils.security import get_current_user_id

router = APIRouter(prefix="/nutrition-scanner", tags=["nutrition-scanner"])
HISTORY_COLLECTION = "food_scan_history"
HISTORY_LIMIT = 50


class ScanHistoryCreate(BaseModel):
    barcode: str = Field(min_length=8, max_length=14)


def _validate_barcode(barcode: str):
    if not valid_barcode(barcode):
        raise HTTPException(status_code=422, detail="Enter a barcode containing 8–14 digits.")


def _history(db: Session, user_id: int):
    return (
        db.query(UserDataRecord)
        .filter_by(user_id=user_id, collection=HISTORY_COLLECTION)
        .order_by(UserDataRecord.updated_at.desc(), UserDataRecord.id.desc())
        .all()
    )


@router.get("/product/{barcode}")
def lookup(barcode: str, user_id: int = Depends(get_current_user_id)):
    _validate_barcode(barcode)
    try:
        product = get_product(barcode)
    except ScanRateLimited as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from None
    except ScanProviderUnavailable:
        raise HTTPException(status_code=503, detail="Product lookup temporarily unavailable.") from None
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found. Check the barcode or use manual food entry.")
    return product


@router.get("/history")
def list_scan_history(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return [
        {"id": row.id, "barcode": row.data.get("barcode"), "scanned_at": row.data.get("scanned_at")}
        for row in _history(db, user_id)[:HISTORY_LIMIT]
    ]


@router.post("/history")
def save_scan(
    body: ScanHistoryCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    _validate_barcode(body.barcode)
    records = _history(db, user_id)
    for row in records:
        if row.data.get("barcode") == body.barcode:
            row.data = {"barcode": body.barcode, "scanned_at": datetime.now(timezone.utc).isoformat()}
            db.commit()
            db.refresh(row)
            return {"id": row.id, **row.data}
    row = UserDataRecord(
        user_id=user_id,
        collection=HISTORY_COLLECTION,
        data={"barcode": body.barcode, "scanned_at": datetime.now(timezone.utc).isoformat()},
    )
    db.add(row)
    db.flush()
    # Bound user history and prevent unlimited user-data growth.
    for old in records[HISTORY_LIMIT - 1:]:
        db.delete(old)
    db.commit()
    db.refresh(row)
    return {"id": row.id, **row.data}


@router.delete("/history/{record_id}", status_code=204)
def delete_scan(
    record_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    row = (
        db.query(UserDataRecord)
        .filter_by(id=record_id, user_id=user_id, collection=HISTORY_COLLECTION)
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Scan history entry not found.")
    db.delete(row)
    db.commit()
