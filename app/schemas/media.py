from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# Enums
class MediaKind(str, Enum):
    """Тип медиа контента"""

    MOVIE = "movie"
    SERIES = "series"
    COURSE = "course"
    BOOK = "book"
    PODCAST = "podcast"


class WatchStatus(str, Enum):
    """Статус просмотра"""

    TO_WATCH = "to_watch"
    WATCHING = "watching"
    WATCHED = "watched"


class Media(BaseModel):
    """Доменная модель медиа контента"""

    id: int = Field(..., description="Уникальный идентификатор")
    title: str = Field(..., min_length=1, max_length=200, description="Название медиа")
    kind: MediaKind = Field(..., description="Тип медиа контента")
    year: int = Field(..., ge=1800, le=2030, description="Год выпуска")
    description: Optional[str] = Field(None, max_length=1000, description="Описание")
    user_id: int = Field(..., description="ID владельца")
    status: WatchStatus = Field(
        default=WatchStatus.TO_WATCH, description="Статус просмотра"
    )
    rating: Optional[int] = Field(None, ge=1, le=10, description="Рейтинг")
    created_at: datetime = Field(
        default_factory=datetime.now, description="Дата добавления"
    )


class MediaBase(BaseModel):
    """Базовая схема медиа"""

    title: str = Field(..., min_length=1, max_length=200, description="Название медиа")
    kind: MediaKind = Field(..., description="Тип медиа контента")
    year: int = Field(..., ge=1800, le=2030, description="Год выпуска")
    description: Optional[str] = Field(None, max_length=1000, description="Описание")


class MediaCreate(MediaBase):
    """Схема создания медиа"""

    pass


class MediaUpdate(MediaBase):
    """Схема обновления медиа"""

    pass


class MediaStatusUpdate(BaseModel):
    """Схема для обновления статуса"""

    status: WatchStatus = Field(..., description="Новый статус просмотра")
    rating: Optional[int] = Field(None, ge=1, le=10, description="Рейтинг от 1 до 10")


class MediaResponse(MediaBase):
    """Схема ответа API"""

    id: int
    user_id: int
    status: WatchStatus
    rating: Optional[int]
    created_at: str

    model_config = ConfigDict(from_attributes=True)
