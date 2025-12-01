"""SQLAlchemy implementation of UserRepository."""

from typing import Optional

from sqlalchemy.orm import Session

from domain.models import User
from domain.repositories.user_repository import UserRepository
from infrastructure.database.models import UserModel
from infrastructure.mappers import db_user_to_domain, domain_user_to_db


class SQLAlchemyUserRepository(UserRepository):
    """SQLAlchemy implementation of UserRepository interface."""
    
    def __init__(self, session: Session) -> None:
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
    
    def create(self, user: User) -> User:
        """Create a new user."""
        db_user = domain_user_to_db(user)
        self.session.add(db_user)
        self.session.commit()
        self.session.refresh(db_user)
        return db_user_to_domain(db_user)
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        db_user = self.session.query(UserModel).filter(UserModel.id == user_id).first()
        return db_user_to_domain(db_user) if db_user else None
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        db_user = self.session.query(UserModel).filter(UserModel.username == username).first()
        return db_user_to_domain(db_user) if db_user else None
    
    def list_all(self, skip: int = 0, limit: int = 100) -> list[User]:
        """List all users with pagination."""
        db_users = self.session.query(UserModel).offset(skip).limit(limit).all()
        return [db_user_to_domain(db_user) for db_user in db_users]
    
    def update(self, user: User) -> User:
        """Update existing user."""
        db_user = self.session.query(UserModel).filter(UserModel.id == user.id).first()
        if not db_user:
            raise ValueError(f"User with id {user.id} not found")
        
        db_user = domain_user_to_db(user, db_user)
        self.session.commit()
        self.session.refresh(db_user)
        return db_user_to_domain(db_user)
    
    def delete(self, user_id: int) -> bool:
        """Delete user by ID."""
        db_user = self.session.query(UserModel).filter(UserModel.id == user_id).first()
        if not db_user:
            return False
        
        self.session.delete(db_user)
        self.session.commit()
        return True
