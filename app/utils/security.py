from fastapi import Depends
from app.auth.dependencies import get_current_user

def get_current_user_id(user = Depends(get_current_user)) -> int | str | None:
    """
    Returns the authenticated user's ID from the JWT payload.
    Assumes 'sub' in the token is the user ID.
    """
    return user.get("sub")
