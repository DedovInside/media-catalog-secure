from datetime import datetime
from typing import List, Optional

from app.schemas.media import (
    Media,
    MediaCreate,
    MediaKind,
    MediaStatusUpdate,
    MediaUpdate,
    WatchStatus,
)

# In-memory "database" (предполагается замена на реальную БД)
_MEDIA_DB: List[Media] = []
_NEXT_ID = 1


def get_next_id() -> int:
    """Генератор уникальных ID"""
    global _NEXT_ID
    current_id = _NEXT_ID
    _NEXT_ID += 1
    return current_id


def clear_all() -> None:
    """Очистить все данные (для тестов)"""
    global _NEXT_ID
    _MEDIA_DB.clear()
    _NEXT_ID = 1


def get_media_list(
    user_id: int, kind: Optional[MediaKind] = None, status: Optional[WatchStatus] = None
) -> List[Media]:
    """Получить список медиа с фильтрацией"""
    media_list = [media for media in _MEDIA_DB if media.user_id == user_id]

    if kind:
        media_list = [media for media in media_list if media.kind == kind]

    if status:
        media_list = [media for media in media_list if media.status == status]

    return media_list


def get_media_by_id(media_id: int, user_id: int) -> Optional[Media]:
    """Получить медиа по ID для конкретного пользователя"""
    for media in _MEDIA_DB:
        if media.id == media_id and media.user_id == user_id:
            return media
    return None


def check_media_exists(title: str, year: int, kind: MediaKind, user_id: int) -> bool:
    """Проверить существование дубликата медиа"""
    for media in _MEDIA_DB:
        if (
            media.user_id == user_id
            and media.title.lower() == title.lower()
            and media.year == year
            and media.kind == kind
        ):
            return True
    return False


def create_media(media_data: MediaCreate, user_id: int) -> Media:
    """Создать новое медиа"""
    new_media = Media(
        id=get_next_id(),
        user_id=user_id,
        title=media_data.title,
        kind=media_data.kind,
        year=media_data.year,
        description=media_data.description,
        status=WatchStatus.TO_WATCH,
        rating=None,
        created_at=datetime.now(),
    )

    _MEDIA_DB.append(new_media)
    return new_media


def update_media(
    media_id: int, media_data: MediaUpdate, user_id: int
) -> Optional[Media]:
    """Обновить медиа"""
    for i, media in enumerate(_MEDIA_DB):
        if media.id == media_id and media.user_id == user_id:
            updated_media = Media(
                id=media.id,
                user_id=media.user_id,
                title=media_data.title,
                kind=media_data.kind,
                year=media_data.year,
                description=media_data.description,
                status=media.status,  # Сохраняем статус
                rating=media.rating,  # Сохраняем рейтинг
                created_at=media.created_at,  # Сохраняем дату создания
            )
            _MEDIA_DB[i] = updated_media
            return updated_media
    return None


def update_media_status(
    media_id: int, status_data: MediaStatusUpdate, user_id: int
) -> Optional[Media]:
    """Обновить статус просмотра медиа"""
    for i, media in enumerate(_MEDIA_DB):
        if media.id == media_id and media.user_id == user_id:
            updated_media = media.model_copy()
            updated_media.status = status_data.status
            updated_media.rating = status_data.rating

            _MEDIA_DB[i] = updated_media
            return updated_media
    return None


def create_demo_data(user_id: int) -> None:
    """Создать демо-данные"""
    demo_media = [
        MediaCreate(
            title="Die Hard",
            kind=MediaKind.MOVIE,
            year=1988,
            description="Hurricane action movie",
        ),
        MediaCreate(
            title="LOST",
            kind=MediaKind.SERIES,
            year=2004,
            description="Mysterious island series",
        ),
        MediaCreate(
            title="Python Course",
            kind=MediaKind.COURSE,
            year=2025,
            description="Learn Python programming",
        ),
    ]

    for media_data in demo_media:
        create_media(media_data, user_id)


def delete_media(media_id: int, user_id: int) -> bool:
    """Удалить медиа"""
    for i, media in enumerate(_MEDIA_DB):
        if media.id == media_id and media.user_id == user_id:
            _MEDIA_DB.pop(i)
            return True
    return False
