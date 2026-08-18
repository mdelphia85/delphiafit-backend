from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.jwt_handler import decode_access_token
from app.database.connection import get_db
from app.models.coach import Coach


def get_current_coach(
    token_data: dict = Depends(decode_access_token),
    db: Session = Depends(get_db),
) -> Coach:
    if token_data.get("actor_type") != "coach":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Coach access required")
    try:
        coach_id = int(token_data.get("sub"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid coach token")
    coach = db.query(Coach).filter(Coach.id == coach_id, Coach.is_active.is_(True)).first()
    if not coach:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Coach account not found")
    return coach
