"""Post API router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from application.services.post_service import PostService
from application.dtos.post_dtos import PostCreate, PostUpdate, PostView, PostListView
from infrastructure.database.repositories.post_repository import SQLAlchemyPostRepository
from infrastructure.database.repositories.user_repository import SQLAlchemyUserRepository


router = APIRouter(prefix="/posts", tags=["posts"])


def get_post_service(db: Session = Depends(get_db)) -> PostService:
    """Dependency to get post service."""
    post_repo = SQLAlchemyPostRepository(db)
    user_repo = SQLAlchemyUserRepository(db)
    return PostService(post_repo, user_repo)


@router.post("", response_model=PostView, status_code=status.HTTP_201_CREATED)
def create_post(
    post_create: PostCreate,
    service: PostService = Depends(get_post_service),
) -> PostView:
    """
    Create a new post.
    
    Demonstrates:
    - BuildDTO excluding System fields
    - ViewDTO from PostAggregate (Post + User)
    - Author information in response
    """
    try:
        return service.create_post(post_create)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{post_id}", response_model=PostView)
def get_post(
    post_id: int,
    service: PostService = Depends(get_post_service),
) -> PostView:
    """
    Get post by ID with author information.
    
    Demonstrates:
    - ViewDTO from Aggregate[Post, User]
    - Field extraction from multiple domains
    - Computed fields (excerpt)
    """
    post = service.get_post(post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return post


@router.get("", response_model=list[PostListView])
def list_posts(
    skip: int = 0,
    limit: int = 100,
    published_only: bool = False,
    service: PostService = Depends(get_post_service),
) -> list[PostListView]:
    """
    List posts with author information.
    
    Demonstrates:
    - Simplified aggregate ViewDTO for listings
    - Filtering (published_only)
    """
    return service.list_posts(skip, limit, published_only)


@router.patch("/{post_id}", response_model=PostView)
def update_post(
    post_id: int,
    post_update: PostUpdate,
    service: PostService = Depends(get_post_service),
) -> PostView:
    """
    Update existing post.
    
    Demonstrates:
    - BuildDTO with optional fields
    - Automatic updated_at timestamp
    """
    try:
        return service.update_post(post_id, post_update)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{post_id}/publish", response_model=PostView)
def publish_post(
    post_id: int,
    service: PostService = Depends(get_post_service),
) -> PostView:
    """
    Publish a post.
    
    Demonstrates:
    - Domain method usage (post.publish())
    - Business logic in domain layer
    """
    try:
        return service.publish_post(post_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: int,
    service: PostService = Depends(get_post_service),
) -> None:
    """Delete post by ID."""
    if not service.delete_post(post_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
