"""Post DTOs demonstrating aggregates and field mapping."""

from datetime import datetime
from potato import ViewDTO, BuildDTO, Field, computed
from domain.models import Post, User
from domain.aggregates import PostAggregate


class PostView(ViewDTO[PostAggregate]):
    """
    ViewDTO for PostAggregate - demonstrates building from multiple domains.
    
    Features demonstrated:
    - Building from Aggregate[Post, User]
    - Field extraction from multiple domains
    - Mixing direct fields and mapped fields
    """
    # Post fields
    id: int = Field(source=PostAggregate.post.id)
    title: str = Field(source=PostAggregate.post.title)
    content: str = Field(source=PostAggregate.post.content)
    created_at: datetime = Field(source=PostAggregate.post.created_at)
    updated_at: datetime = Field(source=PostAggregate.post.updated_at)
    published: bool = Field(source=PostAggregate.post.published)
    
    # Author fields from User domain
    author_id: int = Field(source=PostAggregate.author.id)
    author_name: str = Field(source=PostAggregate.author.username)
    author_full_name: str = Field(source=PostAggregate.author.full_name)
    
    @computed
    def excerpt(self, aggregate: PostAggregate) -> str:
        """Computed field showing post excerpt (first 100 chars)."""
        content = aggregate.post.content
        return content[:100] + "..." if len(content) > 100 else content


class PostListView(ViewDTO[PostAggregate]):
    """Simplified ViewDTO for post listings."""
    id: int = Field(source=PostAggregate.post.id)
    title: str = Field(source=PostAggregate.post.title)
    author_name: str = Field(source=PostAggregate.author.username)
    published: bool = Field(source=PostAggregate.post.published)
    created_at: datetime = Field(source=PostAggregate.post.created_at)


class PostCreate(BuildDTO[Post]):
    """
    BuildDTO for creating posts.
    
    Features demonstrated:
    - System fields (id, created_at, updated_at) excluded
    """
    title: str
    content: str
    author_id: int
    published: bool = False


class PostUpdate(BuildDTO[Post]):
    """BuildDTO for updating posts with optional fields."""
    title: str | None = None
    content: str | None = None
    published: bool | None = None
