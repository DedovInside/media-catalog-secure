from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.error_handlers import ApiError, setup_exception_handlers
from app.api.media import router as media_router
from app.crud import media as media_crud


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan события приложения"""
    # Startup: создаем демо-данные
    media_crud.create_demo_data(user_id=1)
    yield
    pass


app = FastAPI(
    title="Media Catalog API",
    version="0.1.0",
    description="Каталог фильмов/курсов к просмотру",
    lifespan=lifespan,  # Вместо on_event
)

# Настраиваем обработчик ошибок
setup_exception_handlers(app)

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
