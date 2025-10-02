from typing import List, Optional

from fastapi import APIRouter, Query

from app.api.error_handlers import ApiError
from app.crud import media as media_crud
from app.schemas.media import (
    MediaCreate,
    MediaKind,
    MediaResponse,
    MediaStatusUpdate,
    MediaUpdate,
    WatchStatus,
)

router = APIRouter()


# Заглушка для получения текущего пользователя (заменим в будущем на реальную аутентификацию)
CURRENT_USER_ID = 1


@router.get("", response_model=List[MediaResponse], summary="Получить список медиа")
def get_media(
    kind: Optional[MediaKind] = Query(None, description="Фильтр по типу медиа"),
    status: Optional[WatchStatus] = Query(
        None, description="Фильтр по статусу просмотра"
    ),
) -> List[MediaResponse]:
    """
    Получить список медиа с возможностью фильтрации.

    - **kind**: фильтр по типу медиа (movie, series, course, book, podcast)
    - **status**: фильтр по статусу просмотра (to_watch, watching, watched)
    """
    media_list = media_crud.get_media_list(CURRENT_USER_ID, kind, status)

    # Преобразуем в схему ответа
    return [
        MediaResponse(
            id=media.id,
            title=media.title,
            kind=media.kind,
            year=media.year,
            description=media.description,
            user_id=media.user_id,
            status=media.status,
            rating=media.rating,
            created_at=media.created_at.isoformat(),
        )
        for media in media_list
    ]


@router.get("/{media_id}", response_model=MediaResponse, summary="Получить медиа по ID")
def get_media_by_id(media_id: int) -> MediaResponse:
    """Получить конкретное медиа по ID"""
    media = media_crud.get_media_by_id(media_id, CURRENT_USER_ID)
    if not media:
        raise ApiError(
            code="not_found", message=f"Media with id {media_id} not found", status=404
        )

    return MediaResponse(
        id=media.id,
        title=media.title,
        kind=media.kind,
        year=media.year,
        description=media.description,
        user_id=media.user_id,
        status=media.status,
        rating=media.rating,
        created_at=media.created_at.isoformat(),
    )


@router.post(
    "", response_model=MediaResponse, status_code=201, summary="Добавить новое медиа"
)
def create_media(media_data: MediaCreate) -> MediaResponse:
    """
    Добавить новое медиа в каталог.

    Проверяет дубликаты по названию + год + тип для текущего пользователя.
    """
    # Проверка дубликатов
    if media_crud.check_media_exists(
        media_data.title, media_data.year, media_data.kind, CURRENT_USER_ID
    ):
        raise ApiError(
            code="media_already_exists",
            message=(
                f"Media '{media_data.title}' ({media_data.year}, {media_data.kind}) "
                f"already exists"
            ),
            status=409,
        )

    new_media = media_crud.create_media(media_data, CURRENT_USER_ID)

    return MediaResponse(
        id=new_media.id,
        title=new_media.title,
        kind=new_media.kind,
        year=new_media.year,
        description=new_media.description,
        user_id=new_media.user_id,
        status=new_media.status,
        rating=new_media.rating,
        created_at=new_media.created_at.isoformat(),
    )


@router.put("/{media_id}", response_model=MediaResponse, summary="Обновить медиа")
def update_media(media_id: int, media_data: MediaUpdate) -> MediaResponse:
    """Полное обновление информации о медиа"""
    updated_media = media_crud.update_media(media_id, media_data, CURRENT_USER_ID)
    if not updated_media:
        raise ApiError(
            code="not_found", message=f"Media with id {media_id} not found", status=404
        )

    return MediaResponse(
        id=updated_media.id,
        title=updated_media.title,
        kind=updated_media.kind,
        year=updated_media.year,
        description=updated_media.description,
        user_id=updated_media.user_id,
        status=updated_media.status,
        rating=updated_media.rating,
        created_at=updated_media.created_at.isoformat(),
    )


@router.patch(
    "/{media_id}/status",
    response_model=MediaResponse,
    summary="Изменить статус просмотра",
)
def update_media_status(media_id: int, status_data: MediaStatusUpdate) -> MediaResponse:
    """
    Изменить статус просмотра и рейтинг медиа.

    Позволяет отметить как 'смотрю', 'просмотрено' и поставить оценку.
    """
    updated_media = media_crud.update_media_status(
        media_id, status_data, CURRENT_USER_ID
    )
    if not updated_media:
        raise ApiError(
            code="not_found", message=f"Media with id {media_id} not found", status=404
        )

    return MediaResponse(
        id=updated_media.id,
        title=updated_media.title,
        kind=updated_media.kind,
        year=updated_media.year,
        description=updated_media.description,
        user_id=updated_media.user_id,
        status=updated_media.status,
        rating=updated_media.rating,
        created_at=updated_media.created_at.isoformat(),
    )


@router.delete("/{media_id}", status_code=204, summary="Удалить медиа")
def delete_media(media_id: int):
    """Удалить медиа из каталога"""
    if not media_crud.delete_media(media_id, CURRENT_USER_ID):
        raise ApiError(
            code="not_found", message=f"Media with id {media_id} not found", status=404
        )
