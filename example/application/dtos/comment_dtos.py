"""Comment DTOs demonstrating complex aggregates."""

from datetime import datetime
from potato import ViewDTO, BuildDTO, Field, computed
from domain.models import Comment
from domain.aggregates import CommentAggregate


class CommentView(ViewDTO[CommentAggregate]):
    """
    ViewDTO for CommentAggregate - demonstrates 3-domain aggregates.

    Features demonstrated:
    - Building from field-based Aggregate with 3 domains
    - Field extraction from 3 different domains
    - Type-safe field mapping
    """
    # Comment fields
    id: int = Field(source=CommentAggregate.comment.id)
    content: str = Field(source=CommentAggregate.comment.content)
    created_at: datetime = Field(source=CommentAggregate.comment.created_at)

    # Author fields
    author_id: int = Field(source=CommentAggregate.author.id)
    author_name: str = Field(source=CommentAggregate.author.username)

    # Post fields
    post_id: int = Field(source=CommentAggregate.post.id)
    post_title: str = Field(source=CommentAggregate.post.title)

    @computed
    def author_display(self, aggregate: CommentAggregate) -> str:
        """Computed field for author display."""
        return f"@{aggregate.author.username}"


class CommentListView(ViewDTO[CommentAggregate]):
    """Simplified ViewDTO for comment listings."""
    id: int = Field(source=CommentAggregate.comment.id)
    content: str = Field(source=CommentAggregate.comment.content)
    author_name: str = Field(source=CommentAggregate.author.username)
    created_at: datetime = Field(source=CommentAggregate.comment.created_at)


class CommentCreate(BuildDTO[Comment]):
    """
    BuildDTO for creating comments.

    Features demonstrated:
    - Auto fields (id, created_at) excluded
    """
    content: str
    author_id: int
    post_id: int


class CommentUpdate(BuildDTO[Comment]):
    """BuildDTO for updating comments."""
    content: str
