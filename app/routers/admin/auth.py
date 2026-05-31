from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
<<<<<<< HEAD
from pydantic import BaseModel

from app.database.connection import get_db
from app.models.user import User
from app.auth.hashing import verify_password
from app.auth.jwt_handler import create_access_token, decode_access_token

router = APIRouter(prefix="/admin", tags=["Admin Auth"])


# -----------------------------
# JSON Login Model
# -----------------------------
class AdminLogin(BaseModel):
    email: str
    password: str


# -----------------------------
# POST /admin/login
# Accepts JSON (matches frontend)
# -----------------------------
@router.post("/login")
def admin_login(data: AdminLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid credentials"
        )

    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid credentials"
        )

    if not getattr(user, "is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not an admin"
        )

    token = create_access_token({"sub": user.email, "is_admin": True})
=======

from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.models.user import User
from app.database.connection import get_db
from app.auth.hashing import hash_password, verify_password
from app.auth.jwt_handler import create_access_token, decode_access_token

router = APIRouter(tags=["Auth"])

# REGISTER
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

# LOGIN
@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()

    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    token = create_access_token({"sub": db_user.email})
>>>>>>> 6cfc273 (updated admin auth.py)

    return {
        "access_token": token,
        "token_type": "bearer"
    }

<<<<<<< HEAD

# -----------------------------
# GET /admin/me
# Validates admin token
# -----------------------------
@router.get("/me")
def admin_me(
=======
# AUTH ME
@router.get("/me")
def get_me(
>>>>>>> 6cfc273 (updated admin auth.py)
    token_data: dict = Depends(decode_access_token),
    db: Session = Depends(get_db)
):
    email = token_data.get("sub")
<<<<<<< HEAD
    is_admin = token_data.get("is_admin")

    if not email or not is_admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin token"
=======

    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
>>>>>>> 6cfc273 (updated admin auth.py)
        )

    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
<<<<<<< HEAD
            detail="Admin not found"
=======
            detail="User not found"
>>>>>>> 6cfc273 (updated admin auth.py)
        )

    return {
        "id": user.id,
<<<<<<< HEAD
        "email": user.email,
        "name": user.name
    }


# -----------------------------
# verify_admin dependency
# Used by all admin-protected routes
# -----------------------------
def verify_admin(token_data: dict = Depends(decode_access_token)):
    if not token_data.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    return token_data
=======
        "email": user.email
    }

@router.post("/admin/login")
def admin_login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()

    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(401, "Invalid admin credentials")

    if not db_user.is_admin:
        raise HTTPException(403, "Not authorized")

    token = create_access_token({"sub": db_user.email, "admin": True})

    return {
        "access_token": token,
        "token_type": "bearer"
    }
>>>>>>> 6cfc273 (updated admin auth.py)
