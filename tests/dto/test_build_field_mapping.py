"""Tests for BuildDTO Field(source=...) mapping."""

import pytest

from potato import BuildDTO, Domain, Field


class User(Domain):
    id: int
    username: str
    email: str
    bio: str = ""


class Address(Domain):
    street: str
    city: str
    zip_code: str


class TestBuildFieldMapping:
    """Test Field(source=...) in BuildDTO."""

    def test_basic_rename_to_domain(self) -> None:
        """Field(source=User.username) maps 'login' → 'username' in to_domain()."""

        class UserCreate(BuildDTO[User]):
            login: str = Field(source=User.username)
            email: str

        dto = UserCreate(login="alice", email="alice@example.com")
        user = dto.to_domain(id=1)

        assert user.username == "alice"
        assert user.email == "alice@example.com"
        assert user.id == 1

    def test_rename_with_apply_to(self) -> None:
        """Field mapping works with partial apply_to()."""

        class UserUpdate(BuildDTO[User], partial=True):
            login: str = Field(source=User.username)

        existing = User(id=1, username="bob", email="bob@example.com")
        dto = UserUpdate(login="alice")
        updated = dto.apply_to(existing)

        assert updated.username == "alice"
        assert updated.email == "bob@example.com"
        assert updated.id == 1

    def test_mix_mapped_and_unmapped(self) -> None:
        """Mix of mapped and unmapped fields works correctly."""

        class UserCreate(BuildDTO[User]):
            login: str = Field(source=User.username)
            email: str
            bio: str

        dto = UserCreate(login="alice", email="alice@example.com", bio="Hello!")
        user = dto.to_domain(id=1)

        assert user.username == "alice"
        assert user.email == "alice@example.com"
        assert user.bio == "Hello!"

    def test_kwargs_override_mapping(self) -> None:
        """kwargs in to_domain() override mapped values."""

        class UserCreate(BuildDTO[User]):
            login: str = Field(source=User.username)
            email: str

        dto = UserCreate(login="alice", email="alice@example.com")
        user = dto.to_domain(id=1, username="overridden")

        assert user.username == "overridden"

    def test_deep_path_raises_type_error(self) -> None:
        """Deep paths in BuildDTO Field(source=...) raise TypeError."""
        from potato.types import FieldProxy

        deep_proxy = FieldProxy(User, "city", path=["address", "city"])

        with pytest.raises(TypeError, match="BuildDTO only supports flat field references"):

            class BadDTO(BuildDTO[User]):
                city: str = Field(source=deep_proxy)

    def test_invalid_domain_field_raises_type_error(self) -> None:
        """Referencing a non-existent domain field raises TypeError."""
        from potato.types import FieldProxy

        fake_proxy = FieldProxy(User, "nonexistent", path=["nonexistent"])

        with pytest.raises(TypeError, match="does not exist"):

            class BadDTO(BuildDTO[User]):
                bad_field: str = Field(source=fake_proxy)

    def test_mapping_with_exclude(self) -> None:
        """Field mapping works with exclude parameter."""

        class UserCreate(BuildDTO[User], exclude=["bio"]):
            login: str = Field(source=User.username)
            email: str

        dto = UserCreate(login="alice", email="alice@example.com")
        user = dto.to_domain(id=1)

        assert user.username == "alice"
        assert user.email == "alice@example.com"

    def test_no_mapping_still_works(self) -> None:
        """BuildDTO without Field(source=...) still works normally."""

        class UserCreate(BuildDTO[User]):
            username: str
            email: str

        dto = UserCreate(username="alice", email="alice@example.com")
        user = dto.to_domain(id=1)

        assert user.username == "alice"

    def test_multiple_mappings(self) -> None:
        """Multiple field mappings work together."""

        class UserCreate(BuildDTO[User]):
            login: str = Field(source=User.username)
            mail: str = Field(source=User.email)

        dto = UserCreate(login="alice", mail="alice@example.com")
        user = dto.to_domain(id=1)

        assert user.username == "alice"
        assert user.email == "alice@example.com"
