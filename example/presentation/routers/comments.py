"""Comment API router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from application.services.comment_service import CommentService
from application.dtos.comment_dtos import CommentCreate, CommentUpdate, CommentView, CommentListView
from infrastructure.database.repositories.comment_repository import SQLAlchemyCommentRepository
from infrastructure.database.repositories.user_repository import SQLAlchemyUserRepository
from infrastructure.database.repositories.post_repository import SQLAlchemyPostRepository


router = APIRouter(tags=["comments"])


def get_comment_service(db: Session = Depends(get_db)) -> CommentService:
    """Dependency to get comment service."""
    comment_repo = SQLAlchemyCommentRepository(db)
    user_repo = SQLAlchemyUserRepository(db)
    post_repo = SQLAlchemyPostRepository(db)
    return CommentService(comment_repo, user_repo, post_repo)


@router.post("/posts/{post_id}/comments", response_model=CommentView, status_code=status.HTTP_201_CREATED)
def create_comment(
    post_id: int,
    comment_create: CommentCreate,
    service: CommentService = Depends(get_comment_service),
) -> CommentView:
    """
    Create a new comment on a post.
    
    Demonstrates:
    - ViewDTO from 3-domain aggregate (Comment + User + Post)
    - Cross-domain validation
    - Rich response with full context
    """
    # Ensure post_id matches
    if comment_create.post_id != post_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Post ID in URL must match post_id in body"
        )
    
    try:
        return service.create_comment(comment_create)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/comments/{comment_id}", response_model=CommentView)
def get_comment(
    comment_id: int,
    service: CommentService = Depends(get_comment_service),
) -> CommentView:
    """
    Get comment by ID with full context.
    
    Demonstrates:
    - ViewDTO from CommentAggregate (field-based)
    - Field extraction from 3 domains
    - Computed fields (author_display)
    """
    comment = service.get_comment(comment_id)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    return comment


@router.get("/posts/{post_id}/comments", response_model=list[CommentListView])
def list_comments_by_post(
    post_id: int,
    skip: int = 0,
    limit: int = 100,
    service: CommentService = Depends(get_comment_service),
) -> list[CommentListView]:
    """
    List all comments for a post.
    
    Demonstrates:
    - Aggregate ViewDTO for listings
    - Post filtering
    """
    return service.list_comments_by_post(post_id, skip, limit)


@router.patch("/comments/{comment_id}", response_model=CommentView)
def update_comment(
    comment_id: int,
    comment_update: CommentUpdate,
    service: CommentService = Depends(get_comment_service),
) -> CommentView:
    """Update existing comment."""
    try:
        return service.update_comment(comment_id, comment_update)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: int,
    service: CommentService = Depends(get_comment_service),
) -> None:
    """Delete comment by ID."""
    if not service.delete_comment(comment_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
