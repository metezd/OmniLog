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
    PLAN_TO_WATCH = "PLAN_TO_WATCH"  # Planning to watch/play
    IN_PROGRESS = "IN_PROGRESS"  # Currently playing/watching
    COMPLETED = "COMPLETED"  # Finished
    DROPPED = "DROPPED"  # Dropped / Didn't finish


# 1. USER TABLE
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship: One user can have many library entries
    library_entries = relationship(
        "UserLibrary", back_populates="user", cascade="all, delete-orphan"
    )

    # Relationship: Custom lists created by the user (US-06)
    custom_lists = relationship(
        "CustomList", back_populates="user", cascade="all, delete-orphan"
    )

    # Relationship: User's activity diary events (US-07)
    diary_entries = relationship(
        "DiaryEntry", back_populates="user", cascade="all, delete-orphan"
    )


# 2. MEDIA ITEM TABLE (Games and TV Series)
class MediaItem(Base):
    __tablename__ = "media_items"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), index=True, nullable=False)
    media_type = Column(Enum(MediaType), nullable=False)
    poster_url = Column(String(500), nullable=True)
    release_date = Column(String(50), nullable=True)

    # External IDs from IGDB (games) or TMDB (series and movies). Ids of IGDB and TMDB are
    # different number spaces, so the media type is part of the key. Several titles without an
    # outside id are allowed (NULL values are not equal in a unique constraint).
    external_api_id = Column(Integer, index=True, nullable=True)

    __table_args__ = (
        UniqueConstraint("media_type", "external_api_id", name="uq_media_type_external_id"),
    )

    # Relationship: One media item can be in many users' libraries
    library_entries = relationship("UserLibrary", back_populates="media_item")

    # Relationship: Referenced in custom list items
    list_items = relationship("CustomListItem", back_populates="media_item")


# 3. USER LIBRARY TABLE (Watchlist / Association Table)
class UserLibrary(Base):
    __tablename__ = "user_libraries"

    id = Column(Integer, primary_key=True)
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

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "user_id", "media_item_id", name="uq_user_media_entry"
        ),
        CheckConstraint(
            "rating >= 1 AND rating <= 10", name="chk_rating_range"
        ),
    )


# 4. CUSTOM LIST TABLE (US-06)
class CustomList(Base):
    __tablename__ = "custom_lists"

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_user_list_name"),
    )

    # Relationships
    user = relationship("User", back_populates="custom_lists")
    items = relationship(
        "CustomListItem", back_populates="custom_list", cascade="all, delete-orphan"
    )


# 5. CUSTOM LIST ITEMS TABLE (US-06)
class CustomListItem(Base):
    __tablename__ = "custom_list_items"

    id = Column(Integer, primary_key=True)
    list_id = Column(
        Integer, ForeignKey("custom_lists.id", ondelete="CASCADE"), nullable=False
    )
    media_item_id = Column(
        Integer, ForeignKey("media_items.id", ondelete="CASCADE"), nullable=False
    )
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    custom_list = relationship("CustomList", back_populates="items")
    media_item = relationship("MediaItem", back_populates="list_items")

    __table_args__ = (
        UniqueConstraint("list_id", "media_item_id", name="uq_list_media_item"),
    )


# 6. ACTIVITY DIARY TABLE (US-07)
class DiaryEntry(Base):
    __tablename__ = "diary_entries"

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    # Empty for events that are not about one title, such as LIST_CREATED
    media_item_id = Column(
        Integer, ForeignKey("media_items.id", ondelete="CASCADE"), nullable=True
    )
    # One of the DiaryAction values in app/services/diary_service.py
    action = Column(String(50), nullable=False)
    details = Column(String(255), nullable=True)  # e.g. "Rated 9"
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="diary_entries")
    media_item = relationship("MediaItem")