"""Post service implementing business logic for post operations."""

from datetime import datetime
from typing import Optional

from domain.models import Post
from domain.aggregates import PostAggregate
from domain.repositories.post_repository import PostRepository
from domain.repositories.user_repository import UserRepository
from application.dtos.post_dtos import PostCreate, PostUpdate, PostView, PostListView


class PostService:
    """
    Post service encapsulating post-related business logic.
    
    This service demonstrates:
    - Multiple repository dependencies
    - Aggregate building
    - Business validation
    """
    
    def __init__(
        self,
        post_repository: PostRepository,
        user_repository: UserRepository,
    ) -> None:
        """
        Initialize service with repository dependencies.
        
        Args:
            post_repository: Post repository interface
            user_repository: User repository interface
        """
        self.post_repository = post_repository
        self.user_repository = user_repository
    
    def create_post(self, post_create: PostCreate) -> PostView:
        """
        Create a new post.
        
        Args:
            post_create: Post creation DTO
            
        Returns:
            Created post view with author information
            
        Raises:
            ValueError: If author doesn't exist
        """
        # Business logic: Verify author exists
        author = self.user_repository.get_by_id(post_create.author_id)
        if not author:
            raise ValueError(f"Author with id {post_create.author_id} not found")
        
        # Convert DTO to domain model
        post = post_create.to_domain(
            id=0,  # Auto-generated
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        # Persist
        created_post = self.post_repository.create(post)
        
        # Build aggregate and return view
        aggregate = PostAggregate(post=created_post, author=author)
        return PostView.from_domain(aggregate)
    
    def get_post(self, post_id: int) -> Optional[PostView]:
        """
        Get post by ID with author information.
        
        Args:
            post_id: Post ID
            
        Returns:
            Post view with author or None if not found
        """
        post = self.post_repository.get_by_id(post_id)
        if not post:
            return None
        
        # Get author for aggregate
        author = self.user_repository.get_by_id(post.author_id)
        if not author:
            return None
        
        # Build aggregate and return view
        aggregate = PostAggregate(post=post, author=author)
        return PostView.from_domain(aggregate)
    
    def list_posts(
        self,
        skip: int = 0,
        limit: int = 100,
        published_only: bool = False,
    ) -> list[PostListView]:
        """
        List posts with author information.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records
            published_only: If True, only return published posts
            
        Returns:
            List of post views
        """
        posts = self.post_repository.list_all(skip, limit, published_only)
        
        # Build aggregates with authors
        views = []
        for post in posts:
            author = self.user_repository.get_by_id(post.author_id)
            if author:  # Only include if author exists
                aggregate = PostAggregate(post=post, author=author)
                views.append(PostListView.from_domain(aggregate))
        
        return views
    
    def update_post(self, post_id: int, post_update: PostUpdate) -> PostView:
        """
        Update existing post.
        
        Args:
            post_id: Post ID to update
            post_update: Update DTO
            
        Returns:
            Updated post view
            
        Raises:
            ValueError: If post not found
        """
        post = self.post_repository.get_by_id(post_id)
        if not post:
            raise ValueError(f"Post with id {post_id} not found")
        
        # Apply updates
        update_data = post_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(post, field, value)
        
        # Update timestamp
        post.updated_at = datetime.utcnow()
        
        # Persist
        updated_post = self.post_repository.update(post)
        
        # Get author and build aggregate
        author = self.user_repository.get_by_id(updated_post.author_id)
        if not author:
            raise ValueError(f"Author with id {updated_post.author_id} not found")
        
        aggregate = PostAggregate(post=updated_post, author=author)
        return PostView.from_domain(aggregate)
    
    def publish_post(self, post_id: int) -> PostView:
        """
        Publish a post.
        
        Args:
            post_id: Post ID to publish
            
        Returns:
            Published post view
            
        Raises:
            ValueError: If post not found
        """
        post = self.post_repository.get_by_id(post_id)
        if not post:
            raise ValueError(f"Post with id {post_id} not found")
        
        # Business logic: Use domain method
        post.publish()
        post.updated_at = datetime.utcnow()
        
        # Persist
        updated_post = self.post_repository.update(post)
        
        # Build aggregate
        author = self.user_repository.get_by_id(updated_post.author_id)
        if not author:
            raise ValueError(f"Author not found")
        
        aggregate = PostAggregate(post=updated_post, author=author)
        return PostView.from_domain(aggregate)
    
    def delete_post(self, post_id: int) -> bool:
        """
        Delete post by ID.
        
        Args:
            post_id: Post ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        return self.post_repository.delete(post_id)
