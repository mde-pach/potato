"""Domain models representing core business entities."""

from datetime import datetime
from potato import Domain, System


class User(Domain):
    """
    User domain model representing a user in the blog system.
    
    Attributes:
        id: System-generated unique identifier
        username: Unique username for the user
        email: User's email address
        full_name: User's full display name
        created_at: Timestamp when user was created (system-managed)
        is_active: Whether the user account is active
    """
    id: System[int]
    username: str
    email: str
    full_name: str
    created_at: System[datetime]
    is_active: bool = True


class Post(Domain):
    """
    Post domain model representing a blog post.
    
    Attributes:
        id: System-generated unique identifier
        title: Post title
        content: Post content/body
        author_id: ID of the user who authored the post
        created_at: Timestamp when post was created (system-managed)
        updated_at: Timestamp when post was last updated (system-managed)
        published: Whether the post is published or draft
    """
    id: System[int]
    title: str
    content: str
    author_id: int
    created_at: System[datetime]
    updated_at: System[datetime]
    published: bool = False
    
    def publish(self) -> None:
        """Publish the post."""
        self.published = True
    
    def unpublish(self) -> None:
        """Unpublish the post (make it a draft)."""
        self.published = False


class Comment(Domain):
    """
    Comment domain model representing a comment on a blog post.
    
    Attributes:
        id: System-generated unique identifier
        content: Comment content
        author_id: ID of the user who authored the comment
        post_id: ID of the post being commented on
        created_at: Timestamp when comment was created (system-managed)
    """
    id: System[int]
    content: str
    author_id: int
    post_id: int
    created_at: System[datetime]
