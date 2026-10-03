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


# Medya türü ve liste durumları için sabit seçenekler (Enum)
class MediaType(str, enum.Enum):
    GAME = "GAME"
    SERIES = "SERIES"


class WatchStatus(str, enum.Enum):
    PLAN_TO_WATCH = "PLAN_TO_WATCH"  # Oynamayı/İzlemeyi Düşünüyor
    IN_PROGRESS = "IN_PROGRESS"  # Şu an Oynuyor/İzliyor
    COMPLETED = "COMPLETED"  # Bitirdi
    DROPPED = "DROPPED"  # Bıraktı / Yarım Kaldı


# 1. KULLANICI TABLOSU
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # İlişki: Bir kullanıcının birden çok kütüphane kaydı olabilir
    library_entries = relationship(
        "UserLibrary", back_populates="user", cascade="all, delete-orphan"
    )


# 2. MEDYA ÖĞESİ TABLOSU (Oyunlar ve TV Dizileri)
class MediaItem(Base):
    __tablename__ = "media_items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), index=True, nullable=False)
    media_type = Column(Enum(MediaType), nullable=False)
    poster_url = Column(String(500), nullable=True)
    release_date = Column(String(50), nullable=True)

    # Musab'ın dış API'lerden çekeceği harici ID'ler (RAWG ID veya TMDB ID)
    external_api_id = Column(Integer, index=True, nullable=True)

    # İlişki: Bir medya öğesi birden çok kullanıcının listesinde olabilir
    library_entries = relationship("UserLibrary", back_populates="media_item")


# 3. KULLANICI KÜTÜPHANESİ TABLOSU (Takip Listesi / Ara Tablo)
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
    rating = Column(Float, nullable=True)  # 1 ile 10 arası puan
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # İlişkiler
    user = relationship("User", back_populates="library_entries")
    media_item = relationship("MediaItem", back_populates="library_entries")

    # Kısıtlar (Constraints):
    # 1. Bir kullanıcı aynı oyunu/diziyi listesine iki defa ekleyemesin (Unique)
    # 2. Puan verilirse 1 ile 10 arasında olsun (Check)
    __table_args__ = (
        UniqueConstraint(
            "user_id", "media_item_id", name="uq_user_media_entry"
        ),
        CheckConstraint(
            "rating >= 1 AND rating <= 10", name="chk_rating_range"
        ),
    )