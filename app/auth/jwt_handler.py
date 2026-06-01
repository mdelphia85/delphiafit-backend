from datetime import datetime, timedelta
from jose import jwt, JWTError

# -----------------------------
# JWT CONFIG
# -----------------------------
SECRET_KEY = "CHANGE_THIS_SECRET_KEY"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


# -----------------------------
# CREATE ACCESS TOKEN
# -----------------------------
def create_access_token(data: dict):
    """
    Creates a JWT access token with the provided payload.
    Automatically adds an expiration timestamp.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# -----------------------------
# DECODE ACCESS TOKEN
# -----------------------------
def decode_access_token(token: str):
    """
    Decodes a JWT and returns the payload.
    Raises an exception if the token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise Exception("Invalid or expired token")
