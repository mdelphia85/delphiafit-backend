from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.connection import Base

class Reaction(Base):
    __tablename__ = "reactions"

    id = Column(Integer, primary_key=True, index=True)

    # The user who reacted
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Reaction target: either a post or a comment
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=True)
    comment_id = Column(Integer, ForeignKey("comments.id"), nullable=True)

    # Reaction type: like, heart, clap, etc.
    reaction_type = Column(String, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="reactions")
    post = relationship("Post", back_populates="reactions")
    comment = relationship("Comment", back_populates="reactions")
