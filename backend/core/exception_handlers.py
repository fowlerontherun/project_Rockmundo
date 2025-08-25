# File: backend/core/exception_handlers.py
from typing import Any, Dict
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR, HTTP_422_UNPROCESSABLE_ENTITY
from core.errors import AppError

def _problem(detail: Dict[str, Any], status_code: int) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=detail)

def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _handle_app_error(_: Request, exc: AppError):
        return _problem({"code": exc.code, "message": exc.message}, exc.http_status)

    @app.exception_handler(RequestValidationError)
    async def _handle_validation_error(_: Request, exc: RequestValidationError):
        return _problem({
            "code": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "errors": exc.errors(),
        }, HTTP_422_UNPROCESSABLE_ENTITY)

    @app.exception_handler(HTTPException)
    async def _handle_http_exception(_: Request, exc: HTTPException):
        if isinstance(exc.detail, dict) and "code" in exc.detail and "message" in exc.detail:
            return _problem(exc.detail, exc.status_code)
        return _problem({"code": "HTTP_ERROR", "message": str(exc.detail)}, exc.status_code)

    @app.exception_handler(Exception)
    async def _handle_uncaught(_: Request, exc: Exception):
        return _problem({"code": "INTERNAL_SERVER_ERROR", "message": "An unexpected error occurred"}, HTTP_500_INTERNAL_SERVER_ERROR)
