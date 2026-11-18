from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.jwt_handler import get_active_access_token, verify_token
from app.auth.errors import authentication_database_error
from app.database.connection import get_db
from app.models.coach import Coach
from app.models.client import Client
from app.models.user import User

_optional_bearer = HTTPBearer(auto_error=False)


def _coach_from_token_data(token_data: dict, db: Session, request: Request) -> Coach:
    if token_data.get("actor_type") != "coach":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Coach access required")
    try:
        coach_id = int(token_data.get("sub"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid coach token")
    try:
        coach = db.query(Coach).filter(Coach.id == coach_id).first()
    except Exception as exc:
        raise authentication_database_error(db, request, "coach token validation", exc) from None
    if not coach or not coach.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    if token_data.get("token_version") is None or token_data["token_version"] != coach.token_version:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return coach


def get_current_coach(
    request: Request,
    token_data: dict = Depends(get_active_access_token),
    db: Session = Depends(get_db),
) -> Coach:
    return _coach_from_token_data(token_data, db, request)


def get_optional_current_coach(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_optional_bearer),
    db: Session = Depends(get_db),
) -> Coach | None:
    if credentials is None:
        return None
    token_data = verify_token(credentials.credentials)
    if token_data is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return _coach_from_token_data(token_data, db, request)


def get_current_client(
    request: Request,
    token_data: dict = Depends(get_active_access_token),
    db: Session = Depends(get_db),
) -> Client:
    """Resolve the coaching Client record for a regular user token (matched by email)."""
    if token_data.get("actor_type") not in (None, "user"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Client account required")
    try:
        user_id = int(token_data.get("sub"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user token")
    try:
        user = db.query(User).filter(User.id == user_id).first()
    except Exception as exc:
        raise authentication_database_error(db, request, "client user lookup", exc) from None
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account not found")
    try:
        client = db.query(Client).filter(Client.email == user.email, Client.status != "inactive").first()
    except Exception as exc:
        raise authentication_database_error(db, request, "client account lookup", exc) from None
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="You are not linked to a coach yet")
    return client
