from typing import List
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.api.problem import problem

class StrictContentTypeMiddleware(BaseHTTPMiddleware):
    """Middleware для строгой проверки Content-Type"""
    
    def __init__(self, app, allowed_types: List[str] = None):
        super().__init__(app)
        self.allowed_types = allowed_types or ["application/json"]

    async def dispatch(self, request: Request, call_next):
        # Проверяем только POST/PUT/PATCH запросы
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "").split(";")[0].strip()
            
            if content_type not in self.allowed_types:
                error_response = problem(
                    status=415,
                    detail=f"Content-Type must be one of: {', '.join(self.allowed_types)}"
                )
                return JSONResponse(
                    status_code=415, 
                    content=error_response
                )
        
        # Продолжаем обработку
        response = await call_next(request)
        return response