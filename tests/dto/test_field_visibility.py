"""Tests for Field(visible=...) with context."""

from potato import Field, ViewDTO, Domain


class Permissions:
    def __init__(self, is_admin: bool = False):
        self.is_admin = is_admin


class User(Domain):
    id: int
    username: str
    email: str


class TestFieldVisibility:
    """Test Field(visible=...) functionality."""

    def test_visible_field_shown_when_predicate_true(self) -> None:
        """Test that field is shown when visible predicate returns True."""

        class UserView(ViewDTO[User, Permissions]):
            id: int
            username: str
            email: str = Field(visible=lambda ctx: ctx.is_admin)

        user = User(id=1, username="alice", email="alice@example.com")
        ctx = Permissions(is_admin=True)
        view = UserView.from_domain(user, context=ctx)

        data = view.model_dump()
        assert "email" in data
        assert data["email"] == "alice@example.com"

    def test_visible_field_hidden_when_predicate_false(self) -> None:
        """Test that field is hidden when visible predicate returns False."""

        class UserView(ViewDTO[User, Permissions]):
            id: int
            username: str
            email: str = Field(visible=lambda ctx: ctx.is_admin)

        user = User(id=1, username="alice", email="alice@example.com")
        ctx = Permissions(is_admin=False)
        view = UserView.from_domain(user, context=ctx)

        data = view.model_dump()
        assert "email" not in data

    def test_visible_field_hidden_when_no_context(self) -> None:
        """Test that field is hidden when no context is provided."""

        class UserView(ViewDTO[User, Permissions | None]):
            id: int
            username: str
            email: str = Field(visible=lambda ctx: ctx.is_admin)

        user = User(id=1, username="alice", email="alice@example.com")
        view = UserView.from_domain(user)

        data = view.model_dump()
        assert "email" not in data

    def test_multiple_visible_fields(self) -> None:
        """Test multiple fields with visibility predicates."""

        class UserView(ViewDTO[User, Permissions]):
            id: int
            username: str = Field(visible=lambda ctx: True)
            email: str = Field(visible=lambda ctx: ctx.is_admin)

        user = User(id=1, username="alice", email="alice@example.com")
        ctx = Permissions(is_admin=False)
        view = UserView.from_domain(user, context=ctx)

        data = view.model_dump()
        assert "username" in data
        assert "email" not in data
