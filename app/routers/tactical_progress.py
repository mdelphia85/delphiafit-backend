import re
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.tactical_progress import TacticalProgress
from app.utils.security import get_current_user_id

router = APIRouter(prefix="/tactical/progress", tags=["Tactical Progress"])
_MODULE = re.compile(r"^[a-z0-9_-]{1,80}$")
_ITEM_KEY = re.compile(r"^[a-zA-Z0-9._:-]{1,120}$")


class ProgressPayload(BaseModel):
    item_key: str = "state"
    data: Any


def _validate_key(module: str, item_key: str) -> None:
    if not _MODULE.fullmatch(module) or not _ITEM_KEY.fullmatch(item_key):
        raise HTTPException(status_code=422, detail="Invalid tactical progress key")


@router.get("/{module}")
def get_progress(
    module: str,
    item_key: str = Query(default="state", min_length=1, max_length=120),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    _validate_key(module, item_key)
    row = db.query(TacticalProgress).filter_by(user_id=user_id, module=module, item_key=item_key).first()
    return {"module": module, "item_key": item_key, "data": row.data if row else None}


@router.put("/{module}")
def save_progress(
    module: str,
    payload: ProgressPayload,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    _validate_key(module, payload.item_key)
    row = db.query(TacticalProgress).filter_by(user_id=user_id, module=module, item_key=payload.item_key).first()
    if row is None:
        row = TacticalProgress(user_id=user_id, module=module, item_key=payload.item_key, data=payload.data)
        db.add(row)
    else:
        row.data = payload.data
    db.commit()
    db.refresh(row)
    return {"module": module, "item_key": payload.item_key, "data": row.data}
