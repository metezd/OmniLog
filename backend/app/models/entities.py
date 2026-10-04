import enum
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Enum,
    Float,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.orm import relationship
from app.core.database import Base


# Media types and tracking statuses
class MediaType(str, enum.Enum):
    GAME = "GAME"
    SERIES = "SERIES"
    MOVIE = "MOVIE"


class WatchStatus(str, enum.Enum):
    PLAN_TO_WATCH = "PLAN_TO_WATCH"  # Planing to watch/play
    IN_PROGRESS = "IN_PROGRESS"  # Currently playing/watching
    COMPLETED = "COMPLETED"  # Finished
    DROPPED = "DROPPED"  # Dropped / Didn't finish


# 1. USER TABLE
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship: One user can have many library entries
    library_entries = relationship(
        "UserLibrary", back_populates="user", cascade="all, delete-orphan"
    )


# 2. MEDIA ITEM TABLE (Games and TV Series)
class MediaItem(Base):
    __tablename__ = "media_items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), index=True, nullable=False)
    media_type = Column(Enum(MediaType), nullable=False)
    poster_url = Column(String(500), nullable=True)
    release_date = Column(String(50), nullable=True)

    # External IDs from RAWG or TMDB APIs
    external_api_id = Column(Integer, index=True, nullable=True)

    # Relationship: One media item can be in many users' libraries
    library_entries = relationship("UserLibrary", back_populates="media_item")


# 3. USER LIBRARY TABLE (Watchlist / Association Table)
class UserLibrary(Base):
    __tablename__ = "user_libraries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    media_item_id = Column(
        Integer, ForeignKey("media_items.id", ondelete="CASCADE"), nullable=False
    )

    status = Column(
        Enum(WatchStatus), default=WatchStatus.PLAN_TO_WATCH, nullable=False
    )
    rating = Column(Float, nullable=True)  # Rating between 1 and 10
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user = relationship("User", back_populates="library_entries")
    media_item = relationship("MediaItem", back_populates="library_entries")

    # Constraints:
    # 1. Prevent duplicate entries for the same user and media item
    # 2. Restrict rating value between 1 and 10
    __table_args__ = (
        UniqueConstraint(
            "user_id", "media_item_id", name="uq_user_media_entry"
        ),
        CheckConstraint(
            "rating >= 1 AND rating <= 10", name="chk_rating_range"
        ),
    )