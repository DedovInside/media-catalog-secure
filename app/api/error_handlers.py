from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse


# Перенёс сюда обработку ошибок API для централизованного управления из main.py
class ApiError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        self.code = code
        self.message = message
        self.status = status


def setup_exception_handlers(app: FastAPI):
    """Настройка обработчиков исключений"""

    @app.exception_handler(ApiError)
    async def api_error_handler(request: Request, exc: ApiError):
        return JSONResponse(
            status_code=exc.status,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        # Normalize FastAPI HTTPException into our error envelope
        detail = exc.detail if isinstance(exc.detail, str) else "http_error"
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": "http_error", "message": detail}},
        )
