from typing import Any, Dict
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from .errors import ErrorResponse, ValidationErrorItem
import uuid, time


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:12]}"
        start = time.perf_counter()
        request.state.request_id = req_id
        response = await call_next(request)
        duration_ms = int((time.perf_counter() - start) * 1000)
        response.headers["X-Request-ID"] = req_id
        response.headers["X-Response-Time"] = str(duration_ms)
        return response


def _http_exception_handler(request: Request, exc):
    status_code = getattr(exc, "status_code", 500)
    err_code = {
        400: "bad_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        409: "conflict",
        415: "unsupported_media_type",
        429: "rate_limited",
        500: "server_error",
    }.get(status_code, "server_error")
    body = ErrorResponse(
        error=err_code, message=str(getattr(exc, "detail", "An error occurred.")), request_id=getattr(request.state, "request_id", None)
    ).model_dump()
    return JSONResponse(status_code=status_code, content=body)


def _validation_exception_handler(request: Request, exc: RequestValidationError):
    items = []
    for e in exc.errors():
        loc = [str(x) for x in e.get("loc", [])]
        items.append(ValidationErrorItem(loc=loc, msg=e.get("msg", ""), type=e.get("type", "")))
    body = ErrorResponse(
        error="validation_error", message="Request failed validation.", request_id=getattr(request.state, "request_id", None), validation=items
    ).model_dump()
    return JSONResponse(status_code=422, content=body)


def apply_openapi_customizations(app: FastAPI) -> None:
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"], expose_headers=["X-Request-ID", "X-Response-Time"])
    from fastapi.exceptions import HTTPException
    app.add_exception_handler(HTTPException, _http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, _validation_exception_handler)
    if not app.openapi_schema:
        app.openapi()
    schema: Dict[str, Any] = dict(app.openapi_schema)
    components = schema.setdefault("components", {})
    security_schemes = components.setdefault("securitySchemes", {})
    security_schemes["bearerAuth"] = {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
    schema["servers"] = [{"url": "{{baseUrl}}", "description": "Environment base URL"}]
    app.openapi_schema = schema


def add_auth_example(route) -> None:
    extra = getattr(route, "openapi_extra", {}) or {}
    headers = extra.get("headers", {})
    headers["Authorization"] = {"schema": {"type": "string", "example": "Bearer {{token}}"}, "description": "Bearer token (JWT)."}
    extra["headers"] = headers
    setattr(route, "openapi_extra", extra)
