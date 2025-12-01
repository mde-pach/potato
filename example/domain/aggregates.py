"""Domain aggregates for composing multiple domains."""

from potato import Aggregate
from domain.models import User, Post, Comment


class PostAggregate(Aggregate[Post, User]):
    """
    Post aggregate combining a post with its author.
    
    This aggregate represents a complete view of a post including
    the author information for rich displays.
    
    Attributes:
        post: The post entity
        author: The user who authored the post
    """
    post: Post
    author: User


class CommentAggregate(Aggregate[Comment, User, Post]):
    """
    Comment aggregate combining a comment with its author and related post.
    
    This aggregate provides full context for a comment including
    who wrote it and what post it belongs to.
    
    Attributes:
        comment: The comment entity
        author: The user who authored the comment
        post: The post being commented on
    """
    comment: Comment
    author: User
    post: Post
