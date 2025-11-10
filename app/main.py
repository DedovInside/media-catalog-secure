import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.error_handlers import ApiError, setup_exception_handlers
from app.api.media import router as media_router
from app.core.database import AsyncSessionLocal, create_tables
from app.crud import media_crud
from app.middleware.content_type import StrictContentTypeMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan события приложения"""
    env = os.getenv("ENV", "local").lower()
    try:
        if env == "test":
            await create_tables()
            yield
        elif env == "ci":
            await create_tables()
            yield
        else:
            await create_tables()
            try:
                async with AsyncSessionLocal() as db:
                    await media_crud.create_demo_data(db, user_id=1)
            except Exception as e:
                print(f"[lifespan] Demo data creation failed: {e}")
            yield
    except Exception as e:
        print(f"[lifespan] Unexpected error: {e}")
        yield


app = FastAPI(
    title="Media Catalog API",
    version="0.1.0",
    description="Каталог фильмов/курсов к просмотру",
    lifespan=lifespan,  # Вместо on_event
)

# Настраиваем обработчик ошибок
setup_exception_handlers(app)

# Регистрируем middleware для строгой проверки Content-Type
app.add_middleware(StrictContentTypeMiddleware, allowed_types=["application/json"])

# Регистрируем роутеры
app.include_router(media_router, prefix="/media", tags=["media"])


@app.get("/health")
def health():
    return {"status": "ok"}


_DB = {"items": []}


@app.post("/items")
def create_item(name: str):

    if not name or len(name) > 100:
        raise ApiError(
            code="validation_error",  # Безопасное сообщение из SAFE_ERROR_DETAILS
            status=422,
        )
    item = {"id": len(_DB["items"]) + 1, "name": name}
    _DB["items"].append(item)
    return item


@app.get("/items/{item_id}")
def get_item(item_id: int):
    from app.api.error_handlers import ApiError

    for it in _DB["items"]:
        if it["id"] == item_id:
            return it
    raise ApiError(code="not_found", status=404)  # Без message
