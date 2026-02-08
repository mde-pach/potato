"""Comment service implementing business logic for comment operations."""

from datetime import datetime
from typing import Optional

from domain.models import Comment
from domain.aggregates import CommentAggregate
from domain.repositories.comment_repository import CommentRepository
from domain.repositories.user_repository import UserRepository
from domain.repositories.post_repository import PostRepository
from application.dtos.comment_dtos import CommentCreate, CommentUpdate, CommentView, CommentListView


class CommentService:
    """
    Comment service encapsulating comment-related business logic.
    
    This service demonstrates:
    - Three repository dependencies
    - Complex aggregate building (3 domains)
    - Cross-domain validation
    """
    
    def __init__(
        self,
        comment_repository: CommentRepository,
        user_repository: UserRepository,
        post_repository: PostRepository,
    ) -> None:
        """
        Initialize service with repository dependencies.
        
        Args:
            comment_repository: Comment repository interface
            user_repository: User repository interface
            post_repository: Post repository interface
        """
        self.comment_repository = comment_repository
        self.user_repository = user_repository
        self.post_repository = post_repository
    
    def create_comment(self, comment_create: CommentCreate) -> CommentView:
        """
        Create a new comment.
        
        Args:
            comment_create: Comment creation DTO
            
        Returns:
            Created comment view with author and post information
            
        Raises:
            ValueError: If author or post doesn't exist
        """
        # Business logic: Verify author exists
        author = self.user_repository.get_by_id(comment_create.author_id)
        if not author:
            raise ValueError(f"Author with id {comment_create.author_id} not found")
        
        # Business logic: Verify post exists
        post = self.post_repository.get_by_id(comment_create.post_id)
        if not post:
            raise ValueError(f"Post with id {comment_create.post_id} not found")
        
        # Convert DTO to domain model
        comment = comment_create.to_domain(
            id=0,  # Auto-generated
            created_at=datetime.utcnow(),
        )
        
        # Persist
        created_comment = self.comment_repository.create(comment)
        
        # Build 3-domain aggregate and return view
        aggregate = CommentAggregate(
            comment=created_comment,
            author=author,
            post=post,
        )
        return CommentView.from_domain(aggregate)
    
    def get_comment(self, comment_id: int) -> Optional[CommentView]:
        """
        Get comment by ID with full context.
        
        Args:
            comment_id: Comment ID
            
        Returns:
            Comment view with author and post or None if not found
        """
        comment = self.comment_repository.get_by_id(comment_id)
        if not comment:
            return None
        
        # Get author and post for aggregate
        author = self.user_repository.get_by_id(comment.author_id)
        post = self.post_repository.get_by_id(comment.post_id)
        
        if not author or not post:
            return None
        
        # Build aggregate
        aggregate = CommentAggregate(comment=comment, author=author, post=post)
        return CommentView.from_domain(aggregate)
    
    def list_comments_by_post(
        self,
        post_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> list[CommentListView]:
        """
        List comments for a specific post.
        
        Args:
            post_id: Post ID
            skip: Number of records to skip
            limit: Maximum number of records
            
        Returns:
            List of comment views
        """
        comments = self.comment_repository.list_by_post(post_id, skip, limit)
        
        # Build aggregates
        views = []
        for comment in comments:
            author = self.user_repository.get_by_id(comment.author_id)
            post = self.post_repository.get_by_id(comment.post_id)
            
            if author and post:
                aggregate = CommentAggregate(comment=comment, author=author, post=post)
                views.append(CommentListView.from_domain(aggregate))
        
        return views
    
    def update_comment(self, comment_id: int, comment_update: CommentUpdate) -> CommentView:
        """
        Update existing comment.
        
        Args:
            comment_id: Comment ID to update
            comment_update: Update DTO
            
        Returns:
            Updated comment view
            
        Raises:
            ValueError: If comment not found
        """
        comment = self.comment_repository.get_by_id(comment_id)
        if not comment:
            raise ValueError(f"Comment with id {comment_id} not found")
        
        # Apply updates
        comment.content = comment_update.content
        
        # Persist
        updated_comment = self.comment_repository.update(comment)
        
        # Build aggregate
        author = self.user_repository.get_by_id(updated_comment.author_id)
        post = self.post_repository.get_by_id(updated_comment.post_id)
        
        if not author or not post:
            raise ValueError("Author or post not found")
        
        aggregate = CommentAggregate(comment=updated_comment, author=author, post=post)
        return CommentView.from_domain(aggregate)
    
    def delete_comment(self, comment_id: int) -> bool:
        """
        Delete comment by ID.
        
        Args:
            comment_id: Comment ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        return self.comment_repository.delete(comment_id)
