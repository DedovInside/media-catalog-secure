from typing import List, Optional

from sqlalchemy import and_, delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.media import MediaModel
from app.schemas.media import MediaCreate, MediaKind, MediaStatusUpdate, MediaUpdate, WatchStatus


class MediaCRUD:
    """Async CRUD operations for Media with user isolation"""

    async def get_media_list(
        self,
        db: AsyncSession,
        user_id: int,
        kind: Optional[MediaKind] = None,
        status: Optional[WatchStatus] = None,
    ) -> List[MediaModel]:
        """Get media list with filtering and user isolation (NFR-06)"""
        query = select(MediaModel).where(MediaModel.user_id == user_id)

        if kind:
            query = query.where(MediaModel.kind == kind)
        if status:
            query = query.where(MediaModel.status == status)

        # Сортировка по дате создания (новые сначала)
        query = query.order_by(MediaModel.created_at.desc())

        result = await db.execute(query)
        return result.scalars().all()

    async def get_media_by_id(
        self, db: AsyncSession, media_id: int, user_id: int
    ) -> Optional[MediaModel]:
        """Get media by ID with user isolation (NFR-06)"""
        query = select(MediaModel).where(
            and_(MediaModel.id == media_id, MediaModel.user_id == user_id)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def check_media_exists(
        self, db: AsyncSession, title: str, year: int, kind: MediaKind, user_id: int
    ) -> bool:
        """Check if media already exists for user (duplicate prevention)"""
        query = select(MediaModel).where(
            and_(
                MediaModel.user_id == user_id,
                func.lower(MediaModel.title) == func.lower(title),  # Case-insensitive
                MediaModel.year == year,
                MediaModel.kind == kind,
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none() is not None

    async def create_media(
        self, db: AsyncSession, media_data: MediaCreate, user_id: int
    ) -> MediaModel:
        """Create new media with user isolation"""
        new_media = MediaModel(
            title=media_data.title,
            kind=media_data.kind,
            year=media_data.year,
            description=media_data.description,
            user_id=user_id,  # 🔒 User isolation (NFR-06)
            status=WatchStatus.TO_WATCH,
            rating=None,
        )

        db.add(new_media)
        try:
            await db.commit()
            await db.refresh(new_media)
            return new_media
        except IntegrityError:
            await db.rollback()
            # Log the actual error for debugging but don't expose it
            # logger.error(f"Database integrity error: {e}")
            raise  # Re-raise for duplicate handling

    async def update_media(
        self, db: AsyncSession, media_id: int, media_data: MediaUpdate, user_id: int
    ) -> Optional[MediaModel]:
        """Update media with user isolation"""
        media = await self.get_media_by_id(db, media_id, user_id)
        if not media:
            return None

        # Update fields
        media.title = media_data.title
        media.kind = media_data.kind
        media.year = media_data.year
        media.description = media_data.description

        try:
            await db.commit()
            await db.refresh(media)
            return media
        except IntegrityError:
            await db.rollback()
            raise

    async def update_media_status(
        self,
        db: AsyncSession,
        media_id: int,
        status_data: MediaStatusUpdate,
        user_id: int,
    ) -> Optional[MediaModel]:
        """Update media status with user isolation"""
        media = await self.get_media_by_id(db, media_id, user_id)
        if not media:
            return None

        media.status = status_data.status
        media.rating = status_data.rating

        try:
            await db.commit()
            await db.refresh(media)
            return media
        except IntegrityError:
            await db.rollback()
            raise

    async def delete_media(self, db: AsyncSession, media_id: int, user_id: int) -> bool:
        """Delete media with user isolation"""
        media = await self.get_media_by_id(db, media_id, user_id)
        if not media:
            return False

        await db.delete(media)
        await db.commit()
        return True

    async def create_demo_data(self, db: AsyncSession, user_id: int) -> None:
        """Create demo data for development"""
        demo_media = [
            MediaCreate(
                title="Die Hard",
                kind=MediaKind.MOVIE,
                year=1988,
                description="Action movie",
            ),
            MediaCreate(
                title="LOST",
                kind=MediaKind.SERIES,
                year=2004,
                description="Mystery series",
            ),
            MediaCreate(
                title="Python Course",
                kind=MediaKind.COURSE,
                year=2025,
                description="Programming course",
            ),
        ]

        for media_data in demo_media:
            # Check if already exists to avoid duplicates
            exists = await self.check_media_exists(
                db, media_data.title, media_data.year, media_data.kind, user_id
            )
            if not exists:
                await self.create_media(db, media_data, user_id)

    async def clear_all(self, db: AsyncSession) -> None:
        """Clear all data (for tests only)"""
        await db.execute(delete(MediaModel))
        await db.commit()


# Singleton instance
media_crud = MediaCRUD()
