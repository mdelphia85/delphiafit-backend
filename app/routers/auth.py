from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.models.user import User
from app.database.connection import get_db
from app.auth.hashing import hash_password, verify_password
from app.auth.jwt_handler import create_access_token, decode_access_token

router = APIRouter(tags=["Auth"])

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

    token = create_access_token({"sub": db_user.email})

    return {
        "access_token": token,
        "token_type": "bearer"
    }

# ---------------------------------------------------------
# AUTH ME (PUBLIC)
# ---------------------------------------------------------
@router.get("/me")
def get_me(
    token_data: dict = Depends(decode_access_token),
    db: Session = Depends(get_db)
):
    email = token_data.get("sub")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

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
