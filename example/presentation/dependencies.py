"""FastAPI dependencies for dependency injection."""

from typing import Generator
from sqlalchemy.orm import Session

from database import get_db
from domain.repositories.user_repository import UserRepository
from domain.repositories.post_repository import PostRepository
from domain.repositories.comment_repository import CommentRepository
from infrastructure.database.repositories.user_repository import SQLAlchemyUserRepository
from infrastructure.database.repositories.post_repository import SQLAlchemyPostRepository
from infrastructure.database.repositories.comment_repository import SQLAlchemyCommentRepository
from application.services.user_service import UserService
from application.services.post_service import PostService
from application.services.comment_service import CommentService


# Repository Dependencies

def get_user_repository(db: Session = next(get_db())) -> UserRepository:
    """Get user repository instance."""
    return SQLAlchemyUserRepository(db)


def get_post_repository(db: Session = next(get_db())) -> PostRepository:
    """Get post repository instance."""
    return SQLAlchemyPostRepository(db)


def get_comment_repository(db: Session = next(get_db())) -> CommentRepository:
    """Get comment repository instance."""
    return SQLAlchemyCommentRepository(db)


# Service Dependencies

def get_user_service(db: Session = next(get_db())) -> UserService:
    """Get user service instance."""
    user_repo = SQLAlchemyUserRepository(db)
    return UserService(user_repo)


def get_post_service(db: Session = next(get_db())) -> PostService:
    """Get post service instance."""
    post_repo = SQLAlchemyPostRepository(db)
    user_repo = SQLAlchemyUserRepository(db)
    return PostService(post_repo, user_repo)


def get_comment_service(db: Session = next(get_db())) -> CommentService:
    """Get comment service instance."""
    comment_repo = SQLAlchemyCommentRepository(db)
    user_repo = SQLAlchemyUserRepository(db)
    post_repo = SQLAlchemyPostRepository(db)
    return CommentService(comment_repo, user_repo, post_repo)
