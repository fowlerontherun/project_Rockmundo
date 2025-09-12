from typing import Dict, Any
from fastapi import status
from .errors import ErrorResponse

def std_error_responses(*, include_422: bool = True) -> Dict[int | str, Dict[str, Any]]:
    responses: Dict[int | str, Dict[str, Any]] = {
        status.HTTP_400_BAD_REQUEST: {
            "description": "Bad Request",
            "model": ErrorResponse,
            "content": {"application/json": {"examples": {"bad_request": {"value": {"error": "bad_request", "message": "Invalid query parameter 'q'.", "request_id": "req_1234abcd"}}}}},
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized",
            "model": ErrorResponse,
            "headers": {"WWW-Authenticate": {"schema": {"type": "string"}, "description": "Bearer"}},
            "content": {"application/json": {"examples": {"unauthorized": {"value": {"error": "unauthorized", "message": "Missing or invalid bearer token.", "request_id": "req_5678efgh"}}}}},
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "Forbidden",
            "model": ErrorResponse,
            "content": {"application/json": {"examples": {"forbidden": {"value": {"error": "forbidden", "message": "You do not have permission to access this resource.", "request_id": "req_abcd9999"}}}}},
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Not Found",
            "model": ErrorResponse,
            "content": {"application/json": {"examples": {"not_found": {"value": {"error": "not_found", "message": "Resource not found.", "request_id": "req_404404"}}}}},
        },
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "description": "Too Many Requests",
            "model": ErrorResponse,
            "headers": {"Retry-After": {"schema": {"type": "integer"}, "description": "Seconds until retry"}},
            "content": {"application/json": {"examples": {"rate_limited": {"value": {"error": "rate_limited", "message": "Too many requests. Try again later.", "request_id": "req_rate123"}}}}},
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Server error",
            "model": ErrorResponse,
            "content": {"application/json": {"examples": {"server_error": {"value": {"error": "server_error", "message": "An unexpected error occurred.", "request_id": "req_oops001"}}}}},
        },
    }
    if include_422:
        responses[status.HTTP_422_UNPROCESSABLE_ENTITY] = {
            "description": "Validation Error",
            "model": ErrorResponse,
            "content": {"application/json": {"examples": {"validation_error": {"value": {"error": "validation_error", "message": "Request body failed validation.", "validation": [{"loc": ["body", "email"], "msg": "value is not a valid email address", "type": "value_error.email"}], "request_id": "req_val001"}}}}},
        }
    return responses
