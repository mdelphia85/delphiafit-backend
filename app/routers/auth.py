from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
import hashlib
import logging
import secrets
from sqlalchemy.orm import Session

from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.models.user import User
from app.models.login_log import LoginLog
from app.database.connection import get_db
from app.auth.hashing import hash_password, verify_password
from app.auth.dependencies import get_current_user
from app.auth.jwt_handler import create_access_token
from app.services.email_delivery import send_user_password_reset

router = APIRouter(tags=["Auth"])
logger = logging.getLogger(__name__)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    token: str
    new_password: str


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

# ---------------------------------------------------------
# REGISTER
# ---------------------------------------------------------
@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    new_user = User(
        name=user.name,
        email=user.email,
        hashed_password=hash_password(user.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

# ---------------------------------------------------------
# LOGIN (PUBLIC)
# ---------------------------------------------------------
@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()

    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if db_user.is_suspended:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account suspended")

    token = create_access_token({
        "sub": str(db_user.id),
        "email": db_user.email,
        "actor_type": "user",
        "token_version": db_user.token_version,
    })

    db.add(LoginLog(user_id=db_user.id, timestamp=datetime.utcnow()))
    db.commit()

    return {
        "access_token": token,
        "token_type": "bearer"
    }



@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).with_for_update().populate_existing().first()
    if user:
        raw_token = secrets.token_urlsafe(32)
        user.password_reset_token_hash = _token_hash(raw_token)
        user.password_reset_expires_at = datetime.utcnow() + timedelta(hours=1)
        db.commit()
        try:
            if not send_user_password_reset(user.email, raw_token):
                logger.warning("User password recovery email is not configured")
        except Exception:
            logger.warning("Unable to deliver user password recovery email")
    return {"message": "If that account exists, reset instructions have been sent."}


@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    if len(data.new_password) < 10:
        raise HTTPException(status_code=400, detail="Password must be at least 10 characters")
    user = (
        db.query(User)
        .filter(User.email == data.email)
        .with_for_update()
        .populate_existing()
        .first()
    )
    if (
        not user
        or not user.password_reset_token_hash
        or not user.password_reset_expires_at
        or user.password_reset_expires_at < datetime.utcnow()
        or not secrets.compare_digest(user.password_reset_token_hash, _token_hash(data.token))
    ):
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user.hashed_password = hash_password(data.new_password)
    user.token_version = User.token_version + 1
    user.password_reset_token_hash = None
    user.password_reset_expires_at = None
    db.commit()
    return {"message": "Password reset successful"}

# ---------------------------------------------------------
# AUTH ME
# ---------------------------------------------------------
@router.get("/me")
def get_me(
    token_data: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        user_id = int(token_data.get("sub"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    user = db.query(User).filter(User.id == user_id, User.email == token_data.get("email")).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user token")

    return {
        "id": user.id,
        "email": user.email
    }

# ---------------------------------------------------------
# REMOVED: OLD /admin/login ROUTE
# ---------------------------------------------------------
# The admin login now lives ONLY in:
# app/routers/admin/auth.py
# and correctly returns {"is_admin": True}
