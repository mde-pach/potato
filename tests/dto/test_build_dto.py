"""Tests for BuildDTO functionality."""

from __future__ import annotations

from typing import Type

import pytest
from pydantic import ValidationError

from potato.dto import BuildDTO

from ..fixtures.domains import Product, User


# =============================================================================
# BuildDTO Test Classes
# =============================================================================


class UserBuildDTO(BuildDTO[User]):
    """A BuildDTO for creating User domains from external data."""

    username: str
    email: str


class UserBuildWithOptionalDTO(BuildDTO[User]):
    """A BuildDTO that includes optional fields."""

    username: str
    email: str
    tutor: str | None = None
    friends: list[str] = []


class ProductBuildDTO(BuildDTO[Product]):
    """A BuildDTO for creating products."""

    name: str
    description: str


class MinimalUserBuildDTO(BuildDTO[User]):
    """A minimal BuildDTO with just one field."""

    username: str


# =============================================================================
# Test BuildDTO Creation
# =============================================================================


class TestBuildDTOCreation:
    """Test BuildDTO instantiation."""

    def test_create_basic_build_dto(self) -> None:
        """Test creating a basic BuildDTO."""
        dto = UserBuildDTO(username="alice", email="alice@example.com")

        assert dto.username == "alice"
        assert dto.email == "alice@example.com"

    def test_create_build_dto_with_optional_fields(self) -> None:
        """Test creating BuildDTO with optional fields."""
        dto = UserBuildWithOptionalDTO(
            username="bob", email="bob@example.com", tutor="alice", friends=["charlie"]
        )

        assert dto.username == "bob"
        assert dto.tutor == "alice"
        assert dto.friends == ["charlie"]

    def test_create_product_build_dto(self) -> None:
        """Test creating a product BuildDTO."""
        dto = ProductBuildDTO(name="Laptop", description="High-performance laptop")

        assert dto.name == "Laptop"
        assert dto.description == "High-performance laptop"

    def test_create_minimal_build_dto(self) -> None:
        """Test creating minimal BuildDTO."""
        dto = MinimalUserBuildDTO(username="test")

        assert dto.username == "test"


class TestBuildDTOValidation:
    """Test BuildDTO validation."""

    def test_missing_required_field_raises_error(self) -> None:
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            UserBuildDTO(username="test")

        error = exc_info.value
        assert "email" in str(error)

    def test_invalid_type_raises_error(self) -> None:
        """Test that invalid types raise ValidationError."""
        with pytest.raises(ValidationError):
            UserBuildDTO(username=123, email="test@example.com")

    def test_extra_fields_allowed(self) -> None:
        """Test that extra fields are allowed (or ignored)."""
        dto = UserBuildDTO(
            username="test", email="test@example.com", extra_field="ignored"
        )

        assert dto.username == "test"
        assert dto.email == "test@example.com"

    def test_empty_string_allowed(self) -> None:
        """Test that empty strings are allowed."""
        dto = UserBuildDTO(username="", email="")

        assert dto.username == ""
        assert dto.email == ""

    def test_list_field_validation(self) -> None:
        """Test that list fields are validated."""
        dto = UserBuildWithOptionalDTO(
            username="test", email="test@example.com", friends=["friend1", "friend2"]
        )

        assert len(dto.friends) == 2
        assert dto.friends == ["friend1", "friend2"]


class TestBuildDTOToDomain:
    """Test converting BuildDTO to Domain."""

    def test_model_dump_for_domain_creation(self, user_class: Type[User]) -> None:
        """Test using model_dump to create domain."""
        dto = UserBuildDTO(username="alice", email="alice@example.com")
        user = user_class(**dto.model_dump(), id=1)

        assert user.id == 1
        assert user.username == "alice"
        assert user.email == "alice@example.com"

    def test_to_domain_method(self) -> None:
        """Test to_domain conversion."""
        dto = UserBuildDTO(username="alice", email="alice@example.com")
        user = dto.to_domain(id=1)

        assert user.id == 1
        assert user.username == "alice"
        assert user.email == "alice@example.com"

    def test_model_dump_with_optional_fields(self, user_class: Type[User]) -> None:
        """Test model_dump includes optional fields."""
        dto = UserBuildWithOptionalDTO(
            username="bob",
            email="bob@example.com",
            tutor="alice",
            friends=["charlie", "diana"],
        )
        user = user_class(**dto.model_dump(), id=2)

        assert user.id == 2
        assert user.username == "bob"
        assert user.tutor == "alice"
        assert user.friends == ["charlie", "diana"]

    def test_partial_build_dto_requires_additional_fields(
        self, user_class: Type[User]
    ) -> None:
        """Test that partial BuildDTO requires additional fields for domain."""
        dto = MinimalUserBuildDTO(username="test")

        with pytest.raises(ValidationError):
            user_class(**dto.model_dump())

        user = user_class(**dto.model_dump(), id=1, email="test@example.com")
        assert user.username == "test"

    def test_product_build_to_domain(self, product_class: Type[Product]) -> None:
        """Test converting product BuildDTO to domain."""
        dto = ProductBuildDTO(name="Widget", description="A useful widget")
        product = product_class(**dto.model_dump(), id=1)

        assert product.id == 1
        assert product.name == "Widget"
        assert product.description == "A useful widget"


class TestBuildDTOSerialization:
    """Test BuildDTO serialization."""

    def test_model_dump(self) -> None:
        """Test model_dump returns dictionary."""
        dto = UserBuildDTO(username="alice", email="alice@example.com")
        data = dto.model_dump()

        assert isinstance(data, dict)
        assert data["username"] == "alice"
        assert data["email"] == "alice@example.com"

    def test_model_dump_json(self) -> None:
        """Test model_dump_json returns JSON string."""
        dto = UserBuildDTO(username="alice", email="alice@example.com")
        json_str = dto.model_dump_json()

        assert isinstance(json_str, str)
        assert "alice" in json_str

    def test_model_dump_exclude(self) -> None:
        """Test model_dump with exclude option."""
        dto = UserBuildWithOptionalDTO(
            username="alice", email="alice@example.com", tutor="bob"
        )
        data = dto.model_dump(exclude={"tutor"})

        assert "username" in data
        assert "email" in data
        assert "tutor" not in data


class TestBuildDTOWithComplexData:
    """Test BuildDTO with complex data scenarios."""

    def test_nested_lists(self) -> None:
        """Test BuildDTO with complex list data."""
        dto = UserBuildWithOptionalDTO(
            username="test",
            email="test@example.com",
            friends=["friend1", "friend2", "friend3", "friend4", "friend5"],
        )

        assert len(dto.friends) == 5

    def test_unicode_data(self) -> None:
        """Test BuildDTO with unicode data."""
        dto = UserBuildDTO(username="用户名", email="test@例え.jp")

        assert dto.username == "用户名"
        assert "例え" in dto.email

    def test_special_characters(self) -> None:
        """Test BuildDTO with special characters."""
        dto = UserBuildDTO(username="user@#$%", email="test+tag@example.com")

        assert dto.username == "user@#$%"
        assert dto.email == "test+tag@example.com"

    def test_very_long_strings(self) -> None:
        """Test BuildDTO with very long strings."""
        long_username = "a" * 1000
        dto = UserBuildDTO(username=long_username, email="test@example.com")

        assert len(dto.username) == 1000


class TestBuildDTOAutoExclusion:
    """Test BuildDTO Auto field exclusion."""

    def test_build_dto_auto_exclusion(self) -> None:
        """Test that Auto[T] fields are excluded from BuildDTO but required for to_domain."""
        from potato import Auto, BuildDTO, Domain

        class UserWithAuto(Domain):
            id: Auto[int]
            username: str

        UserWithAuto.model_rebuild()

        class UserCreate(BuildDTO[UserWithAuto]):
            username: str

        dto = UserCreate(username="testuser")
        assert not hasattr(dto, "id")

        user = dto.to_domain(id=1)
        assert user.id == 1
        assert user.username == "testuser"


class TestBuildDTOEquality:
    """Test BuildDTO equality."""

    def test_same_data_equal(self) -> None:
        """Test that BuildDTOs with same data are equal."""
        dto1 = UserBuildDTO(username="alice", email="alice@example.com")
        dto2 = UserBuildDTO(username="alice", email="alice@example.com")

        assert dto1 == dto2

    def test_different_data_not_equal(self) -> None:
        """Test that BuildDTOs with different data are not equal."""
        dto1 = UserBuildDTO(username="alice", email="alice@example.com")
        dto2 = UserBuildDTO(username="bob", email="bob@example.com")

        assert dto1 != dto2


class TestBuildDTOImmutability:
    """Test BuildDTO mutability (BuildDTOs are not frozen by default)."""

    def test_can_modify_build_dto_fields(self) -> None:
        """Test that BuildDTO fields can be modified."""
        dto = UserBuildDTO(username="alice", email="alice@example.com")
        dto.username = "bob"

        assert dto.username == "bob"
