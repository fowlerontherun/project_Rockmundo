from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from backend.utils.logging import get_logger

logger = get_logger(__name__)


async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error("HTTPException: %s", exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

