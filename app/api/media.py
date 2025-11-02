from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.error_handlers import ApiError
from app.core.database import get_db  # НОВЫЙ IMPORT
from app.crud.media import media_crud  # Singleton instance
from app.schemas.media import (
    MediaCreate,
    MediaKind,
    MediaResponse,
    MediaStatusUpdate,
    MediaUpdate,
    WatchStatus,
)

router = APIRouter()
CURRENT_USER_ID = 1  # Заглушка для аутентификации


@router.get("", response_model=List[MediaResponse])
async def get_media(  # ASYNC
    kind: Optional[MediaKind] = Query(None),
    status: Optional[WatchStatus] = Query(None),
    db: AsyncSession = Depends(get_db),  # DATABASE DEPENDENCY
) -> List[MediaResponse]:
    """Get media list with filtering"""
    media_list = await media_crud.get_media_list(db, CURRENT_USER_ID, kind, status)

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


@router.get("/{media_id}", response_model=MediaResponse)
async def get_media_by_id(  # ASYNC
    media_id: int, db: AsyncSession = Depends(get_db)
) -> MediaResponse:
    """Get media by ID"""
    media = await media_crud.get_media_by_id(db, media_id, CURRENT_USER_ID)
    if not media:
        raise ApiError(code="not_found", status=404)

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


@router.post("", response_model=MediaResponse, status_code=201)
async def create_media(  # ASYNC
    media_data: MediaCreate, db: AsyncSession = Depends(get_db)
) -> MediaResponse:
    """Create new media"""
    # Check duplicates
    if await media_crud.check_media_exists(
        db, media_data.title, media_data.year, media_data.kind, CURRENT_USER_ID
    ):
        raise ApiError(code="already_exists", status=409)

    new_media = await media_crud.create_media(db, media_data, CURRENT_USER_ID)

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


@router.put("/{media_id}", response_model=MediaResponse)
async def update_media(  # ASYNC
    media_id: int, media_data: MediaUpdate, db: AsyncSession = Depends(get_db)
) -> MediaResponse:
    """Update media"""
    updated_media = await media_crud.update_media(db, media_id, media_data, CURRENT_USER_ID)
    if not updated_media:
        raise ApiError(code="not_found", status=404)

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


@router.patch("/{media_id}/status", response_model=MediaResponse)
async def update_media_status(  # ASYNC
    media_id: int, status_data: MediaStatusUpdate, db: AsyncSession = Depends(get_db)
) -> MediaResponse:
    """Update media status"""
    updated_media = await media_crud.update_media_status(db, media_id, status_data, CURRENT_USER_ID)
    if not updated_media:
        raise ApiError(code="not_found", status=404)

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


@router.delete("/{media_id}", status_code=204)
async def delete_media(media_id: int, db: AsyncSession = Depends(get_db)):  # ASYNC
    """Delete media"""
    if not await media_crud.delete_media(db, media_id, CURRENT_USER_ID):
        raise ApiError(code="not_found", status=404)
