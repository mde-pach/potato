"""Tests for partial BuildDTO and apply_to()."""

from potato import BuildDTO, Domain


class User(Domain):
    id: int
    username: str
    email: str
    bio: str = ""


class TestPartialBuildDTO:
    """Test partial=True makes fields optional."""

    def test_partial_makes_fields_optional(self) -> None:
        """Test that partial=True wraps all fields in Optional with default None."""

        class UserUpdate(BuildDTO[User], partial=True):
            username: str
            email: str
            bio: str

        # All fields should be optional
        dto = UserUpdate()
        assert dto.username is None
        assert dto.email is None
        assert dto.bio is None

    def test_partial_accepts_some_fields(self) -> None:
        """Test that partial DTO accepts only some fields."""

        class UserUpdate(BuildDTO[User], partial=True):
            username: str
            email: str

        dto = UserUpdate(username="new_name")
        assert dto.username == "new_name"
        assert dto.email is None

    def test_partial_exclude_unset(self) -> None:
        """Test that partial DTO correctly excludes unset fields."""

        class UserUpdate(BuildDTO[User], partial=True):
            username: str
            email: str

        dto = UserUpdate(username="new_name")
        data = dto.model_dump(exclude_unset=True)
        assert "username" in data
        assert "email" not in data


class TestApplyTo:
    """Test apply_to() method."""

    def test_apply_to_updates_set_fields(self) -> None:
        """Test that apply_to only updates explicitly set fields."""

        class UserUpdate(BuildDTO[User], partial=True):
            username: str
            email: str
            bio: str

        existing = User(id=1, username="alice", email="alice@example.com", bio="Hello")
        update = UserUpdate(username="alice_updated")

        updated = update.apply_to(existing)

        assert updated.id == 1  # Preserved
        assert updated.username == "alice_updated"  # Updated
        assert updated.email == "alice@example.com"  # Preserved
        assert updated.bio == "Hello"  # Preserved

    def test_apply_to_returns_new_instance(self) -> None:
        """Test that apply_to returns a new domain instance."""

        class UserUpdate(BuildDTO[User], partial=True):
            username: str

        existing = User(id=1, username="alice", email="alice@example.com")
        update = UserUpdate(username="bob")

        updated = update.apply_to(existing)

        assert updated is not existing
        assert updated.username == "bob"
        assert existing.username == "alice"  # Original unchanged

    def test_apply_to_multiple_fields(self) -> None:
        """Test applying updates to multiple fields."""

        class UserUpdate(BuildDTO[User], partial=True):
            username: str
            email: str

        existing = User(id=1, username="alice", email="alice@example.com")
        update = UserUpdate(username="bob", email="bob@example.com")

        updated = update.apply_to(existing)

        assert updated.username == "bob"
        assert updated.email == "bob@example.com"
        assert updated.id == 1
