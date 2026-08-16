from sqlalchemy.orm import Session
from app.models.periodization import PeriodizationBlock
from app.schemas.periodization import PeriodizationBlockCreate

def create_periodization_block(db: Session, user_id: int, data: PeriodizationBlockCreate):
    block = PeriodizationBlock(
        user_id=user_id,
        block_name=data.block_name,
        focus=data.focus,
        start_date=data.start_date,
        end_date=data.end_date
    )
    db.add(block)
    db.commit()
    db.refresh(block)
    return block

def get_periodization_blocks(db: Session, user_id: int):
    return db.query(PeriodizationBlock).filter(PeriodizationBlock.user_id == user_id).all()
