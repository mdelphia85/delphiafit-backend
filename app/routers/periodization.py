from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database.connection import get_db
from app.utils.security import get_current_user_id

from app.schemas.periodization import PeriodizationBlockCreate, PeriodizationBlockRead
from app.crud.periodization import create_periodization_block, get_periodization_blocks

router = APIRouter(prefix="/periodization", tags=["periodization"])

@router.post("/", response_model=PeriodizationBlockRead)
def add_periodization_block(
    payload: PeriodizationBlockCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return create_periodization_block(db, user_id, payload)

@router.get("/", response_model=List[PeriodizationBlockRead])
def list_periodization_blocks(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return get_periodization_blocks(db, user_id)


@router.delete("/{block_id}", status_code=204)
def delete_periodization_block(
    block_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    from fastapi import HTTPException
    from app.models.periodization import PeriodizationBlock

    block = db.query(PeriodizationBlock).filter_by(id=block_id, user_id=user_id).first()
    if block is None:
        raise HTTPException(status_code=404, detail="Training block not found")
    db.delete(block)
    db.commit()
