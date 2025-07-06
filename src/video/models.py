from sqlalchemy import Column, DateTime, ForeignKey, func, Integer, String
from sqlalchemy.orm import relationship

from src.db.session import Base


class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), nullable=False)
    description = Column(String(1024), nullable=True)
    s3_url = Column(String(), nullable=True)
    key = Column(String(), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="videos")
