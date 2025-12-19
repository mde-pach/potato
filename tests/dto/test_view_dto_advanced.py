from potato import ViewDTO, Field, computed
from ..fixtures.domains import User

class TestViewDTOAdvancedFeatures:
    """Tests for advanced ViewDTO features like Field(source=...) and Context."""

    def test_field_mapping(self) -> None:
        """Test mapping fields using Field(source=...)."""
        class UserView(ViewDTO[User]):
            # Map 'username' to 'login' using Field
            login: str = Field(source=User.username)
            # Map 'email' directly
            email: str

        user = User(id=1, username="testuser", email="test@example.com")
        view = UserView.build(user)

        assert view.login == "testuser"
        assert view.email == "test@example.com"

    def test_context_injection(self) -> None:
        """Test context injection in @computed fields."""
        class UserContext:
            def __init__(self, is_admin: bool):
                self.is_admin = is_admin

        class AdminView(ViewDTO[User, UserContext]):
            username: str
            is_admin: bool = Field(compute=lambda: False) # Placeholder

            @computed
            def is_admin(self, context: UserContext) -> bool:
                return context.is_admin

        user = User(id=1, username="admin", email="admin@example.com")
        context = UserContext(is_admin=True)
        
        # We need to pass context to build. 
        # Note: The current implementation of ViewDTO.build might need to be updated to accept context if it doesn't already.
        # Let's check ViewDTO.build signature or how context is passed.
        # Based on previous work, ViewDTO.build(domain, context=...) should work.
        view = AdminView.build(user, context=context)

        assert view.username == "admin"
        assert view.is_admin is True
