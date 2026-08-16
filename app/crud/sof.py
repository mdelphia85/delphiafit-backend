from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.sof import SOF


def create_sof(db: Session, data: dict) -> SOF