from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.jwt_handler import decode_access_token
from app.database.connection import get_db
from app.models.coach import Coach
from app.models.client import Client
from app.models.user import User


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


def get_current_client(
    token_data: dict = Depends(decode_access_token),
    db: Session = Depends(get_db),
) -> Client:
    """Resolve the coaching Client record for a regular user token (matched by email)."""
    if token_data.get("actor_type") not in (None, "user"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Client account required")
    try:
        user_id = int(token_data.get("sub"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user token")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account not found")
    client = db.query(Client).filter(Client.email == user.email, Client.status != "inactive").first()
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="You are not linked to a coach yet")
    return client
