from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.connection import Base

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)

    # The user who wrote the comment
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # The post this comment belongs to
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)

    # Comment content
    content = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="comments")
    post = relationship("Post", back_populates="comments")

    # Reactions on comments (likes, hearts, etc.)
    reactions = relationship("Reaction", back_populates="comment", cascade="all, delete-orphan")
