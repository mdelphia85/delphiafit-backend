from fastapi import Depends, HTTPException, status
from app.auth.dependencies import get_current_user


def get_current_user_id(user=Depends(get_current_user)) -> int:
    subject = user.get("sub")
    try:
        return int(subject)
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user token")
