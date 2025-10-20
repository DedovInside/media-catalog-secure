# app/api/problem.py
import uuid
from typing import Any, Dict, Optional

# HTTP статус → краткий title (стандартные фразы)
HTTP_STATUS_TITLES = {
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    409: "Conflict",
    413: "Payload Too Large",
    415: "Unsupported Media Type",
    422: "Unprocessable Entity",
    429: "Too Many Requests",
    500: "Internal Server Error",
}

# Только детальные сообщения (безопасные)
SAFE_ERROR_DETAILS = {
    "not_found": "The requested resource could not be found",
    "already_exists": "A resource with these properties already exists",
    "validation_error": "The provided data is invalid",
    "unauthorized": "Authentication required",
    "forbidden": "Access to this resource is not allowed",
    "payload_too_large": "Request payload exceeds maximum allowed size",
    "unsupported_media_type": "Content-Type header specifies unsupported media type",
    "rate_limit_exceeded": "Too many requests - rate limit exceeded",
}


def problem(
    status: int,
    title: str = None,
    detail: str = None,
    type_url: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Create RFC 7807 Problem Details response"""

    # Автоматический title из HTTP статуса если не передан
    if not title:
        title = HTTP_STATUS_TITLES.get(status, "Error")

    problem_response = {
        "type": type_url
        or f"https://tools.ietf.org/html/rfc7231#section-6.5.{status//100}",
        "title": title,  # КРАТКИЙ ИЗ HTTP СТАТУСА
        "status": status,
        "detail": detail or "An error occurred",  # ПОДРОБНЫЙ ИЗ ПАРАМЕТРА
        "correlation_id": str(uuid.uuid4()),
    }

    problem_response.update(kwargs)
    return problem_response
