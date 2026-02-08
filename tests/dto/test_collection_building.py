"""Tests for from_domains() batch building."""

from potato import ViewDTO

from ..fixtures.domains import User


class TestFromDomains:
    """Test from_domains() batch building."""

    def test_from_domains_basic(self) -> None:
        """Test building a list of ViewDTOs from domains."""

        class UserView(ViewDTO[User]):
            id: int
            username: str

        users = [
            User(id=1, username="alice", email="a@example.com"),
            User(id=2, username="bob", email="b@example.com"),
        ]

        views = UserView.from_domains(users)

        assert len(views) == 2
        assert views[0].id == 1
        assert views[0].username == "alice"
        assert views[1].id == 2
        assert views[1].username == "bob"

    def test_from_domains_empty_list(self) -> None:
        """Test from_domains with empty list."""

        class UserView(ViewDTO[User]):
            id: int

        views = UserView.from_domains([])
        assert views == []

    def test_from_domains_single_item(self) -> None:
        """Test from_domains with single item."""

        class UserView(ViewDTO[User]):
            id: int
            username: str

        users = [User(id=1, username="alice", email="a@example.com")]
        views = UserView.from_domains(users)

        assert len(views) == 1
        assert views[0].username == "alice"

    def test_from_domains_preserves_order(self) -> None:
        """Test that from_domains preserves order."""

        class UserView(ViewDTO[User]):
            id: int
            username: str

        users = [
            User(id=i, username=f"user{i}", email=f"u{i}@example.com")
            for i in range(10)
        ]
        views = UserView.from_domains(users)

        assert len(views) == 10
        for i, view in enumerate(views):
            assert view.id == i
            assert view.username == f"user{i}"
