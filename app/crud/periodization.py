from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.periodization import PeriodizationBlock
from app.schemas.periodization import PeriodizationBlockCreate, PeriodizationBlockUpdate


def create_periodization_block(db: Session, user_id: int, data: PeriodizationBlockCreate) -> PeriodizationBlock:
    block = PeriodizationBlock(
        user_id=user_id,
        block_name=data.block_name,
        focus=data.focus,
        start_date=data.start_date,
        end_date=data.end_date,
    )
    db.add(block)
    db.commit()
    db.refresh(block)
    return block


def get_periodization_block(db: Session, block_id: int) -> Optional[PeriodizationBlock]:
    return db.query(PeriodizationBlock).filter(PeriodizationBlock.id == block_id).first()


def get_periodization_blocks(db: Session, user_id: int) -> List[PeriodizationBlock]:
    return (
        db.query(PeriodizationBlock)
        .filter(PeriodizationBlock.user_id == user_id)
        .order_by(PeriodizationBlock.start_date.desc())
        .all()
    )


def update_periodization_block(db: Session, block_id: int, data: PeriodizationBlockUpdate) -> Optional[PeriodizationBlock]:
    block = get_periodization_block(db, block_id)
    if not block:
        return None

    for field, value in data.dict(exclude_unset=True).items():
        setattr(block, field, value)

    db.commit()
    db.refresh(block)
    return block


def delete_periodization_block(db: Session, block_id: int) -> bool:
    block = get_periodization_block(db, block_id)
    if not block:
        return False

    db.delete(block)
    db.commit()
    return True
