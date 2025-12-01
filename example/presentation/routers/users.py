"""User API router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from application.services.user_service import UserService
from application.dtos.user_dtos import UserCreate, UserUpdate, UserView, UserListView
from infrastructure.database.repositories.user_repository import SQLAlchemyUserRepository


router = APIRouter(prefix="/users", tags=["users"])


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """Dependency to get user service."""
    user_repo = SQLAlchemyUserRepository(db)
    return UserService(user_repo)


@router.post("", response_model=UserView, status_code=status.HTTP_201_CREATED)
def create_user(
    user_create: UserCreate,
    service: UserService = Depends(get_user_service),
) -> UserView:
    """
    Create a new user.
    
    Demonstrates:
    - BuildDTO for input validation
    - ViewDTO for response
    - System fields (id, created_at) auto-generated
    """
    try:
        return service.create_user(user_create)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{user_id}", response_model=UserView)
def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
) -> UserView:
    """
    Get user by ID.
    
    Demonstrates:
    - ViewDTO with computed fields (display_name, account_age_days)
    - Field mapping (login from username)
    """
    user = service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.get("", response_model=list[UserListView])
def list_users(
    skip: int = 0,
    limit: int = 100,
    service: UserService = Depends(get_user_service),
) -> list[UserListView]:
    """
    List all users.
    
    Demonstrates:
    - Simplified ViewDTO for list endpoints
    """
    return service.list_users(skip, limit)


@router.patch("/{user_id}", response_model=UserView)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    service: UserService = Depends(get_user_service),
) -> UserView:
    """
    Update existing user.
    
    Demonstrates:
    - BuildDTO with optional fields
    - Partial updates
    """
    try:
        return service.update_user(user_id, user_update)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
) -> None:
    """Delete user by ID."""
    if not service.delete_user(user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
