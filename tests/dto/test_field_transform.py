"""Tests for Field(transform=...)."""

from datetime import datetime

from potato import Field, ViewDTO, Domain


class TestFieldTransform:
    """Test Field(transform=...) functionality."""

    def test_basic_transform(self) -> None:
        """Test transforming a field value."""

        class User(Domain):
            username: str

        class UserView(ViewDTO[User]):
            username: str = Field(source=User.username, transform=lambda x: x.upper())

        user = User(username="alice")
        view = UserView.from_domain(user)

        assert view.username == "ALICE"

    def test_transform_type_conversion(self) -> None:
        """Test transform that changes the type."""

        class Event(Domain):
            name: str
            timestamp: datetime

        class EventView(ViewDTO[Event]):
            name: str
            timestamp: str = Field(
                source=Event.timestamp,
                transform=lambda dt: dt.isoformat(),
            )

        dt = datetime(2025, 1, 15, 12, 0, 0)
        event = Event(name="Deploy", timestamp=dt)
        view = EventView.from_domain(event)

        assert view.name == "Deploy"
        assert view.timestamp == "2025-01-15T12:00:00"

    def test_transform_with_auto_mapped_field(self) -> None:
        """Test transform on a field that would otherwise auto-map."""

        class User(Domain):
            id: int
            email: str

        class UserView(ViewDTO[User]):
            id: int
            email: str = Field(source=User.email, transform=lambda e: e.split("@")[0])

        user = User(id=1, email="alice@example.com")
        view = UserView.from_domain(user)

        assert view.id == 1
        assert view.email == "alice"
