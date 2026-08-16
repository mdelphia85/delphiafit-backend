from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.connection import Base

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)

    # The user who created the post
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Optional: posts can belong to a group
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)

    # Post content
    content = Column(Text, nullable=False)
    media_url = Column(String, nullable=True)  # image/video/etc.

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="posts")
    group = relationship("Group", back_populates="posts", lazy="joined")

    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    reactions = relationship("Reaction", back_populates="post", cascade="all, delete-orphan")


# Add posts relationship to Group model
# (This is safe even if Group is already defined — SQLAlchemy resolves it)
Group.posts = relationship("Post", back_populates="group")
