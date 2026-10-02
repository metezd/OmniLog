from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


# Association table for relationship between lists and media
list_media_association = Table(
    "list_media_association",
    Base.metadata,
    Column("list_id", Integer, ForeignKey("custom_lists.id"), primary_key=True),
    Column("media_id", Integer, ForeignKey("media.id"), primary_key=True),
)


class CustomList(Base):
    __tablename__ = "custom_lists"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # List info
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    is_public = Column(Integer, default=0)  # Boolean: 0=private, 1=public
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="lists")
    media = relationship(
        "Media",
        secondary=list_media_association,
        backref="custom_lists"
    )
    
    def __repr__(self):
        return f"<CustomList(id={self.id}, name={self.name}, user_id={self.user_id})>"
