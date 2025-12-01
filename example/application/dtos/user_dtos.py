"""User DTOs demonstrating potato's ViewDTO and BuildDTO features."""

from datetime import datetime
from potato import ViewDTO, BuildDTO, Field, computed
from domain.models import User


class UserView(ViewDTO[User]):
    """
    ViewDTO for User - demonstrates field mapping and computed fields.
    
    Features demonstrated:
    - Field mapping: 'login' mapped from 'username'
    - Computed field: 'display_name' derived from username
    - System fields included in output (id, created_at)
    """
    id: int
    login: str = Field(source=User.username)  # Field mapping example
    email: str
    full_name: str
    created_at: datetime
    is_active: bool
    
    @computed
    def display_name(self, user: User) -> str:
        """Computed field showing user's display name."""
        return f"@{user.username}"
    
    @computed
    def account_age_days(self, user: User) -> int:
        """Computed field showing account age in days."""
        return (datetime.utcnow() - user.created_at).days


class UserListView(ViewDTO[User]):
    """Simplified ViewDTO for user listings."""
    id: int
    login: str = Field(source=User.username)
    full_name: str
    is_active: bool


class UserCreate(BuildDTO[User]):
    """
    BuildDTO for creating users - demonstrates System field exclusion.
    
    Features demonstrated:
    - System fields (id, created_at) automatically excluded
    - Validation via Pydantic
    - to_domain() conversion
    """
    username: str
    email: str
    full_name: str
    is_active: bool = True


class UserUpdate(BuildDTO[User]):
    """BuildDTO for updating users with optional fields."""
    username: str | None = None
    email: str | None = None
    full_name: str | None = None
    is_active: bool | None = None
