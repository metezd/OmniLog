from sqlalchemy import Column, Integer, String, DateTime, Text, Enum, Float, Date, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum
from app.db.base import Base


class MediaType(str, PyEnum):
    """Media türü enum"""
    GAME = "game"
    TV_SERIES = "tv_series"


class Media(Base):
    __tablename__ = "media"
    
    id = Column(Integer, primary_key=True, index=True)
    type = Column(Enum(MediaType), nullable=False, index=True)
    
    # External APIs
    external_id = Column(String(100), index=True)  # IGDB game_id or TMDB series_id
    
    # Metadata
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    cover_url = Column(String(500))
    release_date = Column(Date)
    
    # Ratings & Stats
    imdb_rating = Column(Float)
    average_user_rating = Column(Float, default=0.0)
    
    # Flexible metadata
    metadata = Column(JSON, default={})  # genres, developers, platforms, etc.
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    episodes = relationship("Episode", back_populates="media", cascade="all, delete-orphan")
    logs = relationship("Log", back_populates="media", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Media(id={self.id}, type={self.type}, title={self.title})>"
