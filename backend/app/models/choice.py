from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class UserChoice(Base):
    __tablename__ = "user_choices"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    episode_id = Column(Integer, ForeignKey("episodes.id"), nullable=False, index=True)
    
    # Choice tracking
    choice_key = Column(String(100), nullable=False)  # e.g., "ending_choice", "ally_selection"
    choice_value = Column(String(255), nullable=False)  # e.g., "ending_a", "save_sarah"
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="choices")
    episode = relationship("Episode", back_populates="choices")
    
    def __repr__(self):
        return f"<UserChoice(id={self.id}, user={self.user_id}, choice={self.choice_key}={self.choice_value})>"
