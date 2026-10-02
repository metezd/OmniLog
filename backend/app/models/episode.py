from sqlalchemy import Column, Integer, String, DateTime, Text, Date, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class Episode(Base):
    __tablename__ = "episodes"
    
    id = Column(Integer, primary_key=True, index=True)
    media_id = Column(Integer, ForeignKey("media.id"), nullable=False, index=True)
    
    # Episode info
    external_id = Column(String(100))  # IGDB/TMDB episode ID
    episode_number = Column(Integer, nullable=False)
    season_number = Column(Integer)  #
    
    title = Column(String(255), nullable=False)
    description = Column(Text)
    air_date = Column(Date)
    duration_minutes = Column(Integer)  # TV episodes or chapter duration
    
    # Stats
    average_rating = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    media = relationship("Media", back_populates="episodes")
    logs = relationship("Log", back_populates="episode", cascade="all, delete-orphan")
    choices = relationship("UserChoice", back_populates="episode", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Episode(id={self.id}, media_id={self.media_id}, number={self.episode_number})>"
