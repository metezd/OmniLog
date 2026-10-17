import enum
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Enum,
    Float,
    Index,
    SmallInteger,
    UniqueConstraint,
    CheckConstraint,
    text,
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


class ChapterKind(str, enum.Enum):
    EPISODE = "EPISODE"  # An episode of a season of a series
    CHAPTER = "CHAPTER"  # A chapter of an episodic game


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

    # When the seasons and episodes were last loaded from the outside service (US-09). Empty
    # until then. A search result alone does not set it, because a search does not give seasons.
    last_synced = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("media_type", "external_api_id", name="uq_media_type_external_id"),
    )

    # Relationship: One media item can be in many users' libraries
    library_entries = relationship("UserLibrary", back_populates="media_item")

    # Relationship: Referenced in custom list items
    list_items = relationship("CustomListItem", back_populates="media_item")

    # Relationship: The seasons of a series, in season order (US-09). The rows are removed by the
    # database (ON DELETE CASCADE), so the ORM does not load them just to delete them.
    seasons = relationship(
        "Season",
        back_populates="media_item",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Season.season_number",
    )

    # Relationship: The chapters of an episodic game, in chapter order (US-09). Episodes are not
    # included: they belong to a season. Read only, because chapters are written on their own.
    chapters = relationship(
        "Chapter",
        primaryjoin="and_(MediaItem.id == Chapter.media_item_id, Chapter.season_id.is_(None))",
        order_by="Chapter.number",
        viewonly=True,
    )


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
    # Progress of the chapters of this title (US-10). The database cascades the delete.
    chapter_progress = relationship(
        "ChapterProgress",
        back_populates="library_entry",
        primaryjoin="UserLibrary.id == ChapterProgress.library_entry_id",
        foreign_keys="ChapterProgress.library_entry_id",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "user_id", "media_item_id", name="uq_user_media_entry"
        ),
        # Lets chapter_progress point to the entry and its title together (US-10, BR-11)
        UniqueConstraint(
            "id", "media_item_id", name="uq_user_library_id_media_item"
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


# 7. SEASON TABLE (US-09)
class Season(Base):
    __tablename__ = "seasons"

    id = Column(Integer, primary_key=True)
    media_item_id = Column(
        Integer, ForeignKey("media_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Season 0 is used by TMDB for specials
    season_number = Column(Integer, nullable=False)
    title = Column(String(200), nullable=True)
    air_date = Column(String(50), nullable=True)

    __table_args__ = (
        UniqueConstraint("media_item_id", "season_number", name="uq_season_media_number"),
    )

    # Relationships
    media_item = relationship("MediaItem", back_populates="seasons")
    episodes = relationship(
        "Chapter",
        back_populates="season",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Chapter.number",
    )


# 8. CHAPTER TABLE: episodes of a series and chapters of a game (US-09)
class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(Integer, primary_key=True)
    # The series or the game. Episodes keep it too, so a chapter always points to its title.
    media_item_id = Column(
        Integer, ForeignKey("media_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Empty for the chapters of a game
    season_id = Column(
        Integer, ForeignKey("seasons.id", ondelete="CASCADE"), nullable=True, index=True
    )
    number = Column(Integer, nullable=False)
    kind = Column(Enum(ChapterKind), nullable=False)
    title = Column(String(200), nullable=True)
    release_date = Column(String(50), nullable=True)
    runtime_minutes = Column(Integer, nullable=True)
    # Id of the episode at TMDB. Games have no outside source for chapters.
    external_id = Column(Integer, nullable=True)

    __table_args__ = (
        # The number is unique inside a season. A season id that is NULL is never equal to
        # another NULL, so game chapters need the partial index below.
        UniqueConstraint("season_id", "number", name="uq_chapter_season_number"),
        # Lets chapter_progress point to the chapter and its title together (US-10, BR-11)
        UniqueConstraint("id", "media_item_id", name="uq_chapter_id_media_item"),
        Index(
            "uq_chapter_game_number",
            "media_item_id",
            "number",
            unique=True,
            postgresql_where=text("season_id IS NULL"),
            sqlite_where=text("season_id IS NULL"),
        ),
        # An episode belongs to a season, a game chapter does not
        CheckConstraint(
            "(kind = 'EPISODE' AND season_id IS NOT NULL)"
            " OR (kind = 'CHAPTER' AND season_id IS NULL)",
            name="chk_chapter_kind_season",
        ),
        CheckConstraint("number >= 0", name="chk_chapter_number"),
        CheckConstraint(
            "runtime_minutes IS NULL OR runtime_minutes >= 0", name="chk_chapter_runtime"
        ),
    )

    # Relationships
    media_item = relationship("MediaItem")
    season = relationship("Season", back_populates="episodes")
    # The progress rows of all users for this chapter (US-10). The database cascades the delete.
    progress_entries = relationship(
        "ChapterProgress",
        back_populates="chapter",
        primaryjoin="Chapter.id == ChapterProgress.chapter_id",
        foreign_keys="ChapterProgress.chapter_id",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


# 9. CHAPTER PROGRESS TABLE: the personal record of one user for one chapter (US-10)
class ChapterProgress(Base):
    __tablename__ = "chapter_progress"

    id = Column(Integer, primary_key=True)
    # The library entry of the user and the chapter. Both foreign keys are declared below
    # together with media_item_id, so the database checks that they belong to the same title.
    library_entry_id = Column(Integer, nullable=False)
    chapter_id = Column(Integer, nullable=False, index=True)
    # The title of the library entry and of the chapter (BR-11)
    media_item_id = Column(Integer, nullable=False)
    rating = Column(SmallInteger, nullable=True)  # Whole number between 1 and 5 (BR-10)
    # Total of all playtime entries. US-11 fills it, so it stays 0 until then.
    playtime_minutes = Column(Integer, nullable=False, default=0, server_default=text("0"))
    # UTC, like the other timestamps. The server default also covers inserts outside the ORM.
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=text("timezone('utc', now())"),
        onupdate=datetime.utcnow,
    )

    # The joins use the single id columns. media_item_id is not copied by these relationships,
    # because it belongs to both composite foreign keys. The service sets it from the entry, and
    # the database checks that the entry and the chapter have the same title (BR-11).
    library_entry = relationship(
        "UserLibrary",
        back_populates="chapter_progress",
        primaryjoin="UserLibrary.id == ChapterProgress.library_entry_id",
        foreign_keys=[library_entry_id],
    )
    chapter = relationship(
        "Chapter",
        back_populates="progress_entries",
        primaryjoin="Chapter.id == ChapterProgress.chapter_id",
        foreign_keys=[chapter_id],
    )

    __table_args__ = (
        # A progress row can only join a library entry and a chapter of the same title (BR-11).
        # Deleting the entry or the chapter deletes the progress, as before.
        ForeignKeyConstraint(
            ["library_entry_id", "media_item_id"],
            ["user_libraries.id", "user_libraries.media_item_id"],
            name="fk_progress_entry_title",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["chapter_id", "media_item_id"],
            ["chapters.id", "chapters.media_item_id"],
            name="fk_progress_chapter_title",
            ondelete="CASCADE",
        ),
        # One progress row per library entry and chapter. The row is created by the first
        # rating (or playtime entry) and updated after that.
        UniqueConstraint(
            "library_entry_id", "chapter_id", name="uq_progress_entry_chapter"
        ),
        CheckConstraint(
            "rating IS NULL OR (rating >= 1 AND rating <= 5)", name="chk_progress_rating"
        ),
        CheckConstraint("playtime_minutes >= 0", name="chk_progress_playtime"),
    )
