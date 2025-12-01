"""SQLAlchemy implementation of PostRepository."""

from typing import Optional

from sqlalchemy.orm import Session

from domain.models import Post
from domain.repositories.post_repository import PostRepository
from infrastructure.database.models import PostModel
from infrastructure.mappers import db_post_to_domain, domain_post_to_db


class SQLAlchemyPostRepository(PostRepository):
    """SQLAlchemy implementation of PostRepository interface."""
    
    def __init__(self, session: Session) -> None:
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
    
    def create(self, post: Post) -> Post:
        """Create a new post."""
        db_post = domain_post_to_db(post)
        self.session.add(db_post)
        self.session.commit()
        self.session.refresh(db_post)
        return db_post_to_domain(db_post)
    
    def get_by_id(self, post_id: int) -> Optional[Post]:
        """Get post by ID."""
        db_post = self.session.query(PostModel).filter(PostModel.id == post_id).first()
        return db_post_to_domain(db_post) if db_post else None
    
    def list_all(self, skip: int = 0, limit: int = 100, published_only: bool = False) -> list[Post]:
        """List all posts with pagination."""
        query = self.session.query(PostModel)
        if published_only:
            query = query.filter(PostModel.published == True)
        db_posts = query.offset(skip).limit(limit).all()
        return [db_post_to_domain(db_post) for db_post in db_posts]
    
    def list_by_author(self, author_id: int, skip: int = 0, limit: int = 100) -> list[Post]:
        """List posts by a specific author."""
        db_posts = (
            self.session.query(PostModel)
            .filter(PostModel.author_id == author_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [db_post_to_domain(db_post) for db_post in db_posts]
    
    def update(self, post: Post) -> Post:
        """Update existing post."""
        db_post = self.session.query(PostModel).filter(PostModel.id == post.id).first()
        if not db_post:
            raise ValueError(f"Post with id {post.id} not found")
        
        db_post = domain_post_to_db(post, db_post)
        self.session.commit()
        self.session.refresh(db_post)
        return db_post_to_domain(db_post)
    
    def delete(self, post_id: int) -> bool:
        """Delete post by ID."""
        db_post = self.session.query(PostModel).filter(PostModel.id == post_id).first()
        if not db_post:
            return False
        
        self.session.delete(db_post)
        self.session.commit()
        return True
