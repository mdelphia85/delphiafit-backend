from fastapi import APIRouter, Depends

from app.utils.security import get_current_user_id

router = APIRouter()


@router.get("/test")
def test(user_id: int = Depends(get_current_user_id)):
    return {"status": "ok"}
