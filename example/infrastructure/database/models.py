"""SQLAlchemy database models."""

from datetime import datetime
from typing import List

from sqlalchemy import String, Text, Boolean, Integer, ForeignKey, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class UserModel(Base):
    """SQLAlchemy model for User table."""
    
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relationships
    posts: Mapped[List["PostModel"]] = relationship("PostModel", back_populates="author", cascade="all, delete-orphan")
    comments: Mapped[List["CommentModel"]] = relationship("CommentModel", back_populates="author", cascade="all, delete-orphan")


class PostModel(Base):
    """SQLAlchemy model for Post table."""
    
    __tablename__ = "posts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Relationships
    author: Mapped["UserModel"] = relationship("UserModel", back_populates="posts")
    comments: Mapped[List["CommentModel"]] = relationship("CommentModel", back_populates="post", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("ix_posts_author_id", "author_id"),
        Index("ix_posts_published", "published"),
    )


class CommentModel(Base):
    """SQLAlchemy model for Comment table."""
    
    __tablename__ = "comments"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    post_id: Mapped[int] = mapped_column(Integer, ForeignKey("posts.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    author: Mapped["UserModel"] = relationship("UserModel", back_populates="comments")
    post: Mapped["PostModel"] = relationship("PostModel", back_populates="comments")
    
    # Indexes
    __table_args__ = (
        Index("ix_comments_post_id", "post_id"),
        Index("ix_comments_author_id", "author_id"),
    )
