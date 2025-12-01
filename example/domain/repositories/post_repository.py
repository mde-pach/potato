"""Post repository interface."""

from abc import ABC, abstractmethod
from typing import Optional

from domain.models import Post


class PostRepository(ABC):
    """
    Repository interface for Post domain model.
    
    This defines the contract for post data access without
    specifying implementation details.
    """
    
    @abstractmethod
    def create(self, post: Post) -> Post:
        """
        Create a new post.
        
        Args:
            post: Post domain model to create
            
        Returns:
            Created post with system fields populated
        """
        pass
    
    @abstractmethod
    def get_by_id(self, post_id: int) -> Optional[Post]:
        """
        Get post by ID.
        
        Args:
            post_id: Post ID to lookup
            
        Returns:
            Post if found, None otherwise
        """
        pass
    
    @abstractmethod
    def list_all(self, skip: int = 0, limit: int = 100, published_only: bool = False) -> list[Post]:
        """
        List all posts with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            published_only: If True, only return published posts
            
        Returns:
            List of posts
        """
        pass
    
    @abstractmethod
    def list_by_author(self, author_id: int, skip: int = 0, limit: int = 100) -> list[Post]:
        """
        List posts by a specific author.
        
        Args:
            author_id: Author's user ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of posts by the author
        """
        pass
    
    @abstractmethod
    def update(self, post: Post) -> Post:
        """
        Update existing post.
        
        Args:
            post: Post domain model with updated data
            
        Returns:
            Updated post
        """
        pass
    
    @abstractmethod
    def delete(self, post_id: int) -> bool:
        """
        Delete post by ID.
        
        Args:
            post_id: ID of post to delete
            
        Returns:
            True if deleted, False if not found
        """
        pass
