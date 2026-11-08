import logging
import uuid

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def authentication_database_error(
    db: Session,
    request: Request | None,
    operation: str,
    exc: Exception,
) -> HTTPException:
    request_id = getattr(request.state, "request_id", uuid.uuid4().hex) if request is not None else uuid.uuid4().hex
    try:
        db.rollback()
    except Exception as rollback_exc:
        logger.error(
            "Authentication rollback failed request_id=%s operation=%s exception_type=%s",
            request_id,
            operation,
            type(rollback_exc).__name__,
        )
    logger.error(
        "Authentication database operation failed request_id=%s operation=%s exception_type=%s",
        request_id,
        operation,
        type(exc).__name__,
    )
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Authentication service temporarily unavailable",
    )
