from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Enum, String
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum
from app.db.base import Base


class LogStatus(str, PyEnum):
    WATCHING = "watching"
    COMPLETED = "completed"
    DROPPED = "dropped"
    PLANNING = "planning"


class Log(Base):
    __tablename__ = "user_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    media_id = Column(Integer, ForeignKey("media.id"), nullable=False, index=True)
    episode_id = Column(Integer, ForeignKey("episodes.id"))  # Optional - for episode-specific logging
    
    # Rating and status tracking
    rating = Column(Float)  # 0-5 scale or None
    status = Column(Enum(LogStatus), default=LogStatus.WATCHING, index=True)
    
    # Time tracking
    playtime_minutes = Column(Integer, default=0)  # Total playtime/watch time
    
    # User notes
    notes = Column(String(500))
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="logs")
    media = relationship("Media", back_populates="logs")
    episode = relationship("Episode", back_populates="logs")
    
    def __repr__(self):
        return f"<Log(id={self.id}, user_id={self.user_id}, media_id={self.media_id}, rating={self.rating})>"
