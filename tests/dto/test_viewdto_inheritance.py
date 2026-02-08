"""Tests for ViewDTO inheritance."""

from potato import ViewDTO, Field

from ..fixtures.domains import User


class TestViewDTOInheritance:
    """Test ViewDTO extending ViewDTO."""

    def test_basic_inheritance(self) -> None:
        """Test that child ViewDTO inherits parent fields."""

        class UserSummary(ViewDTO[User]):
            id: int
            username: str

        class UserDetail(UserSummary):
            email: str

        user = User(id=1, username="alice", email="alice@example.com", tutor="bob")
        view = UserDetail.from_domain(user)

        assert view.id == 1
        assert view.username == "alice"
        assert view.email == "alice@example.com"

    def test_inheritance_with_field_mapping(self) -> None:
        """Test that child ViewDTO inherits parent's field mappings."""

        class UserSummary(ViewDTO[User]):
            id: int
            login: str = Field(source=User.username)

        class UserDetail(UserSummary):
            email: str

        user = User(id=1, username="alice", email="alice@example.com")
        view = UserDetail.from_domain(user)

        assert view.id == 1
        assert view.login == "alice"
        assert view.email == "alice@example.com"

    def test_child_can_override_fields(self) -> None:
        """Test that child ViewDTO can override parent fields."""

        class UserSummary(ViewDTO[User]):
            id: int
            username: str

        class UserWithEmail(UserSummary):
            email: str

        user = User(id=1, username="alice", email="alice@example.com")

        summary = UserSummary.from_domain(user)
        assert not hasattr(summary, "email")

        detail = UserWithEmail.from_domain(user)
        assert detail.email == "alice@example.com"
