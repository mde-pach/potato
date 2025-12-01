"""Mappers for converting between domain models and database models."""

from domain.models import User, Post, Comment
from infrastructure.database.models import UserModel, PostModel, CommentModel


def db_user_to_domain(db_user: UserModel) -> User:
    """
    Convert database UserModel to domain User.
    
    Args:
        db_user: SQLAlchemy UserModel instance
        
    Returns:
        Domain User instance
    """
    return User(
        id=db_user.id,
        username=db_user.username,
        email=db_user.email,
        full_name=db_user.full_name,
        created_at=db_user.created_at,
        is_active=db_user.is_active,
    )


def domain_user_to_db(user: User, db_user: UserModel | None = None) -> UserModel:
    """
    Convert domain User to database UserModel.
    
    Args:
        user: Domain User instance
        db_user: Optional existing UserModel to update
        
    Returns:
        SQLAlchemy UserModel instance
    """
    if db_user is None:
        db_user = UserModel()
    
    db_user.username = user.username
    db_user.email = user.email
    db_user.full_name = user.full_name
    db_user.is_active = user.is_active
    
    # System fields are set by database or on creation
    if hasattr(user, "id") and user.id is not None:
        db_user.id = user.id
    if hasattr(user, "created_at") and user.created_at is not None:
        db_user.created_at = user.created_at
    
    return db_user


def db_post_to_domain(db_post: PostModel) -> Post:
    """
    Convert database PostModel to domain Post.
    
    Args:
        db_post: SQLAlchemy PostModel instance
        
    Returns:
        Domain Post instance
    """
    return Post(
        id=db_post.id,
        title=db_post.title,
        content=db_post.content,
        author_id=db_post.author_id,
        created_at=db_post.created_at,
        updated_at=db_post.updated_at,
        published=db_post.published,
    )


def domain_post_to_db(post: Post, db_post: PostModel | None = None) -> PostModel:
    """
    Convert domain Post to database PostModel.
    
    Args:
        post: Domain Post instance
        db_post: Optional existing PostModel to update
        
    Returns:
        SQLAlchemy PostModel instance
    """
    if db_post is None:
        db_post = PostModel()
    
    db_post.title = post.title
    db_post.content = post.content
    db_post.author_id = post.author_id
    db_post.published = post.published
    
    # System fields
    if hasattr(post, "id") and post.id is not None:
        db_post.id = post.id
    if hasattr(post, "created_at") and post.created_at is not None:
        db_post.created_at = post.created_at
    if hasattr(post, "updated_at") and post.updated_at is not None:
        db_post.updated_at = post.updated_at
    
    return db_post


def db_comment_to_domain(db_comment: CommentModel) -> Comment:
    """
    Convert database CommentModel to domain Comment.
    
    Args:
        db_comment: SQLAlchemy CommentModel instance
        
    Returns:
        Domain Comment instance
    """
    return Comment(
        id=db_comment.id,
        content=db_comment.content,
        author_id=db_comment.author_id,
        post_id=db_comment.post_id,
        created_at=db_comment.created_at,
    )


def domain_comment_to_db(comment: Comment, db_comment: CommentModel | None = None) -> CommentModel:
    """
    Convert domain Comment to database CommentModel.
    
    Args:
        comment: Domain Comment instance
        db_comment: Optional existing CommentModel to update
        
    Returns:
        SQLAlchemy CommentModel instance
    """
    if db_comment is None:
        db_comment = CommentModel()
    
    db_comment.content = comment.content
    db_comment.author_id = comment.author_id
    db_comment.post_id = comment.post_id
    
    # System fields
    if hasattr(comment, "id") and comment.id is not None:
        db_comment.id = comment.id
    if hasattr(comment, "created_at") and comment.created_at is not None:
        db_comment.created_at = comment.created_at
    
    return db_comment
