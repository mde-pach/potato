"""Tests for advanced ViewDTO features."""

from potato import Field, ViewDTO, computed

from ..fixtures.domains import User


class TestViewDTOAdvancedFeatures:
    """Tests for advanced ViewDTO features like Field(source=...) and Context."""

    def test_field_mapping(self) -> None:
        """Test mapping fields using Field(source=...)."""

        class UserView(ViewDTO[User]):
            login: str = Field(source=User.username)
            email: str

        user = User(id=1, username="testuser", email="test@example.com")
        view = UserView.from_domain(user)

        assert view.login == "testuser"
        assert view.email == "test@example.com"

    def test_context_injection(self) -> None:
        """Test context injection in @computed fields."""

        class UserContext:
            def __init__(self, is_admin: bool):
                self.is_admin = is_admin

        class AdminView(ViewDTO[User, UserContext]):
            username: str
            is_admin: bool = Field(compute=lambda: False)

            @computed
            def is_admin(self, context: UserContext) -> bool:
                return context.is_admin

        user = User(id=1, username="admin", email="admin@example.com")
        context = UserContext(is_admin=True)

        view = AdminView.from_domain(user, context=context)

        assert view.username == "admin"
        assert view.is_admin is True

    def test_from_domains_batch(self) -> None:
        """Test from_domains batch building."""

        class UserView(ViewDTO[User]):
            id: int
            username: str

        users = [
            User(id=1, username="alice", email="a@example.com"),
            User(id=2, username="bob", email="b@example.com"),
            User(id=3, username="charlie", email="c@example.com"),
        ]

        views = UserView.from_domains(users)

        assert len(views) == 3
        assert views[0].username == "alice"
        assert views[1].username == "bob"
        assert views[2].username == "charlie"
