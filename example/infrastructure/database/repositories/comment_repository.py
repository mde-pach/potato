"""SQLAlchemy implementation of CommentRepository."""

from typing import Optional

from sqlalchemy.orm import Session

from domain.models import Comment
from domain.repositories.comment_repository import CommentRepository
from infrastructure.database.models import CommentModel
from infrastructure.mappers import db_comment_to_domain, domain_comment_to_db


class SQLAlchemyCommentRepository(CommentRepository):
    """SQLAlchemy implementation of CommentRepository interface."""
    
    def __init__(self, session: Session) -> None:
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
    
    def create(self, comment: Comment) -> Comment:
        """Create a new comment."""
        db_comment = domain_comment_to_db(comment)
        self.session.add(db_comment)
        self.session.commit()
        self.session.refresh(db_comment)
        return db_comment_to_domain(db_comment)
    
    def get_by_id(self, comment_id: int) -> Optional[Comment]:
        """Get comment by ID."""
        db_comment = self.session.query(CommentModel).filter(CommentModel.id == comment_id).first()
        return db_comment_to_domain(db_comment) if db_comment else None
    
    def list_by_post(self, post_id: int, skip: int = 0, limit: int = 100) -> list[Comment]:
        """List comments for a specific post."""
        db_comments = (
            self.session.query(CommentModel)
            .filter(CommentModel.post_id == post_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [db_comment_to_domain(db_comment) for db_comment in db_comments]
    
    def list_by_author(self, author_id: int, skip: int = 0, limit: int = 100) -> list[Comment]:
        """List comments by a specific author."""
        db_comments = (
            self.session.query(CommentModel)
            .filter(CommentModel.author_id == author_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [db_comment_to_domain(db_comment) for db_comment in db_comments]
    
    def update(self, comment: Comment) -> Comment:
        """Update existing comment."""
        db_comment = self.session.query(CommentModel).filter(CommentModel.id == comment.id).first()
        if not db_comment:
            raise ValueError(f"Comment with id {comment.id} not found")
        
        db_comment = domain_comment_to_db(comment, db_comment)
        self.session.commit()
        self.session.refresh(db_comment)
        return db_comment_to_domain(db_comment)
    
    def delete(self, comment_id: int) -> bool:
        """Delete comment by ID."""
        db_comment = self.session.query(CommentModel).filter(CommentModel.id == comment_id).first()
        if not db_comment:
            return False
        
        self.session.delete(db_comment)
        self.session.commit()
        return True
