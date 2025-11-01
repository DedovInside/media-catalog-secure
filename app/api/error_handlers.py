from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from .problem import SAFE_ERROR_DETAILS, problem


class ApiError(Exception):
    def __init__(self, code: str, message: str = None, status: int = 400):
        self.code = code
        self.message = message or SAFE_ERROR_DETAILS.get(code, "An error occurred")
        self.status = status


def setup_exception_handlers(app: FastAPI):
    """Настройка обработчиков исключений"""

    # app/api/error_handlers.py
    @app.exception_handler(ApiError)
    async def api_error_handler(request: Request, exc: ApiError):
        response_data = problem(
            status=exc.status,
            # title автоматически: 404 -> "Not Found", 409 -> "Conflict"
            detail=SAFE_ERROR_DETAILS.get(exc.code, "An error occurred"),  # ТОЛЬКО DETAIL
        )
        return JSONResponse(status_code=exc.status, content=response_data)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        response_data = problem(
            status=exc.status_code,
            title="HTTP Error",
            detail="An HTTP error occurred",  # GENERIC MESSAGE
        )
        return JSONResponse(status_code=exc.status_code, content=response_data)

    @app.exception_handler(ValidationError)
    async def pydantic_validation_handler(request: Request, exc: ValidationError):
        """Handle general Pydantic validation errors"""
        response_data = problem(
            status=400,  # Generic bad request for internal validation
            detail=SAFE_ERROR_DETAILS.get("validation_error", "The provided data is invalid"),
        )
        return JSONResponse(status_code=400, content=response_data)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle FastAPI request validation errors - ALWAYS 422"""
        response_data = problem(
            status=422,  # RequestValidationError всегда 422
            detail=SAFE_ERROR_DETAILS.get("validation_error", "The provided data is invalid"),
        )
        return JSONResponse(status_code=422, content=response_data)
