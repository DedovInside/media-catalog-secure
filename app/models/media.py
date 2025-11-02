from sqlalchemy import Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Index, Integer, String
from sqlalchemy.sql import func

from app.schemas.media import MediaKind, WatchStatus

from .base import Base


class MediaModel(Base):
    """SQLAlchemy модель для медиа"""

    __tablename__ = "media"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    kind = Column(SQLEnum(MediaKind), nullable=False, index=True)
    year = Column(Integer, nullable=False)
    description = Column(String(1000), nullable=True)
    user_id = Column(Integer, nullable=False, index=True)  # 🔒 Security: user isolation
    status = Column(SQLEnum(WatchStatus), nullable=False, default=WatchStatus.TO_WATCH)
    rating = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_media_user_title_year", "user_id", "title", "year"),  # Duplicate check
        Index("ix_media_user_kind", "user_id", "kind"),  # Filtering by kind
        Index("ix_media_user_status", "user_id", "status"),  # Filtering by status
        Index("ix_media_user_created", "user_id", "created_at"),  # Ordering by date
        {"extend_existing": True},
    )

    def __repr__(self):
        return f"<MediaModel(id={self.id}, title='{self.title}', user_id={self.user_id})>"
