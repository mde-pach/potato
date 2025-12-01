"""User repository interface."""

from abc import ABC, abstractmethod
from typing import Optional

from domain.models import User


class UserRepository(ABC):
    """
    Repository interface for User domain model.
    
    This defines the contract for user data access without
    specifying implementation details.
    """
    
    @abstractmethod
    def create(self, user: User) -> User:
        """
        Create a new user.
        
        Args:
            user: User domain model to create
            
        Returns:
            Created user with system fields populated
        """
        pass
    
    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID to lookup
            
        Returns:
            User if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username.
        
        Args:
            username: Username to lookup
            
        Returns:
            User if found, None otherwise
        """
        pass
    
    @abstractmethod
    def list_all(self, skip: int = 0, limit: int = 100) -> list[User]:
        """
        List all users with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of users
        """
        pass
    
    @abstractmethod
    def update(self, user: User) -> User:
        """
        Update existing user.
        
        Args:
            user: User domain model with updated data
            
        Returns:
            Updated user
        """
        pass
    
    @abstractmethod
    def delete(self, user_id: int) -> bool:
        """
        Delete user by ID.
        
        Args:
            user_id: ID of user to delete
            
        Returns:
            True if deleted, False if not found
        """
        pass
