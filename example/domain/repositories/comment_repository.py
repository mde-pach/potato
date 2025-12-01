"""Comment repository interface."""

from abc import ABC, abstractmethod
from typing import Optional

from domain.models import Comment


class CommentRepository(ABC):
    """
    Repository interface for Comment domain model.
    
    This defines the contract for comment data access without
    specifying implementation details.
    """
    
    @abstractmethod
    def create(self, comment: Comment) -> Comment:
        """
        Create a new comment.
        
        Args:
            comment: Comment domain model to create
            
        Returns:
            Created comment with system fields populated
        """
        pass
    
    @abstractmethod
    def get_by_id(self, comment_id: int) -> Optional[Comment]:
        """
        Get comment by ID.
        
        Args:
            comment_id: Comment ID to lookup
            
        Returns:
            Comment if found, None otherwise
        """
        pass
    
    @abstractmethod
    def list_by_post(self, post_id: int, skip: int = 0, limit: int = 100) -> list[Comment]:
        """
        List comments for a specific post.
        
        Args:
            post_id: Post ID to get comments for
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of comments on the post
        """
        pass
    
    @abstractmethod
    def list_by_author(self, author_id: int, skip: int = 0, limit: int = 100) -> list[Comment]:
        """
        List comments by a specific author.
        
        Args:
            author_id: Author's user ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of comments by the author
        """
        pass
    
    @abstractmethod
    def update(self, comment: Comment) -> Comment:
        """
        Update existing comment.
        
        Args:
            comment: Comment domain model with updated data
            
        Returns:
            Updated comment
        """
        pass
    
    @abstractmethod
    def delete(self, comment_id: int) -> bool:
        """
        Delete comment by ID.
        
        Args:
            comment_id: ID of comment to delete
            
        Returns:
            True if deleted, False if not found
        """
        pass
