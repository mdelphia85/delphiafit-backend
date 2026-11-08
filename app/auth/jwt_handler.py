from datetime import datetime, timedelta
import os

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.auth.errors import authentication_database_error
from app.models.user import User

SECRET_KEY = os.getenv("JWT_SECRET")
if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET environment variable is required")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


_jwt_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def decode_access_token(
    token: str = Depends(_jwt_oauth2_scheme),
) -> dict:
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return payload


def get_active_access_token(
    request: Request,
    payload: dict = Depends(decode_access_token),
    db: Session = Depends(get_db),
) -> dict:
    if payload.get("actor_type") != "coach":
        try:
            user_id = int(payload.get("sub"))
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )
        try:
            user = db.query(User).filter(User.id == user_id).first()
        except Exception as exc:
            raise authentication_database_error(db, request, "user token validation", exc) from None
        if (
            user is None
            or user.is_suspended
            or (payload.get("email") is not None and payload.get("email") != user.email)
            or payload.get("token_version", 0) != user.token_version
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )
    return payload
