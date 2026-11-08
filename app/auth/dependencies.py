from fastapi import Depends, HTTPException, status

from app.auth.jwt_handler import get_active_access_token


def get_current_user(payload: dict = Depends(get_active_access_token)):
    if payload.get("actor_type") == "coach":
        # Coach tokens carry a coach id in `sub`; never let it act as a user id.
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account required")
    return payload
