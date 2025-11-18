"""Tests for basic Domain model functionality."""

from __future__ import annotations

from typing import Type

import pytest
from pydantic import ValidationError

from ..fixtures.domains import Price, Product, User


class TestBasicDomainCreation:
    """Test basic domain model creation and validation."""

    def test_create_user_with_required_fields(self, simple_user: User) -> None:
        """Test creating a user with only required fields."""
        assert simple_user.id == 1
        assert simple_user.username == "alice"
        assert simple_user.email == "alice@example.com"
        assert simple_user.tutor is None
        assert simple_user.friends == []

    def test_create_user_with_optional_tutor(self, user_with_tutor: User) -> None:
        """Test creating a user with optional tutor field."""
        assert user_with_tutor.id == 2
        assert user_with_tutor.username == "bob"
        assert user_with_tutor.tutor == "alice"

    def test_create_user_with_friends_list(self, user_with_friends: User) -> None:
        """Test creating a user with friends list."""
        assert user_with_friends.friends == ["alice", "bob"]
        assert len(user_with_friends.friends) == 2

    def test_create_complete_user(self, complete_user: User) -> None:
        """Test creating a user with all fields populated."""
        assert complete_user.id == 4
        assert complete_user.username == "diana"
        assert complete_user.email == "diana@example.com"
        assert complete_user.tutor == "alice"
        assert complete_user.friends == ["bob", "charlie"]

    def test_create_product(self, simple_product: Product) -> None:
        """Test creating a product domain."""
        assert simple_product.id == 1
        assert simple_product.name == "Widget"
        assert simple_product.description == "A useful widget"

    def test_create_price(self, usd_price: Price) -> None:
        """Test creating a price domain."""
        assert usd_price.amount == 100
        assert usd_price.currency == "USD"


class TestDomainValidation:
    """Test domain validation and error handling."""

    def test_missing_required_field_raises_error(self, user_class: Type[User]) -> None:
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            user_class(id=1, username="test")

        error = exc_info.value
        assert "email" in str(error)

    def test_invalid_type_raises_error(self, user_class: Type[User]) -> None:
        """Test that invalid field types raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            user_class(id="not_an_int", username="test", email="test@example.com")

        error = exc_info.value
        assert "id" in str(error)

    def test_empty_string_allowed(self, user_class: Type[User]) -> None:
        """Test that empty strings are allowed for string fields."""
        user = user_class(id=1, username="", email="")
        assert user.username == ""
        assert user.email == ""

    def test_negative_id_allowed(self, user_class: Type[User]) -> None:
        """Test that negative IDs are allowed (no validation constraint)."""
        user = user_class(id=-1, username="test", email="test@example.com")
        assert user.id == -1

    def test_list_field_defaults_to_empty(self, user_class: Type[User]) -> None:
        """Test that list fields default to empty list."""
        user = user_class(id=1, username="test", email="test@example.com")
        assert user.friends == []
        assert isinstance(user.friends, list)


class TestDomainModelDump:
    """Test domain model serialization."""

    def test_model_dump_basic(self, simple_user: User) -> None:
        """Test model_dump returns correct dictionary."""
        data = simple_user.model_dump()

        assert data["id"] == 1
        assert data["username"] == "alice"
        assert data["email"] == "alice@example.com"
        assert data["tutor"] is None
        assert data["friends"] == []

    def test_model_dump_with_optional_fields(self, complete_user: User) -> None:
        """Test model_dump with all fields populated."""
        data = complete_user.model_dump()

        assert data["id"] == 4
        assert data["username"] == "diana"
        assert data["email"] == "diana@example.com"
        assert data["tutor"] == "alice"
        assert data["friends"] == ["bob", "charlie"]

    def test_model_dump_exclude_unset(self, simple_user: User) -> None:
        """Test model_dump with exclude_unset option."""
        data = simple_user.model_dump(exclude_unset=True)

        assert "id" in data
        assert "username" in data
        assert "email" in data
        # tutor and friends may or may not be included depending on defaults


class TestDomainImmutability:
    """Test that domain models behave correctly with immutability."""

    def test_can_modify_fields(self, simple_user: User) -> None:
        """Test that domain fields can be modified (not frozen by default)."""
        simple_user.username = "new_username"
        assert simple_user.username == "new_username"

    def test_list_modification(self, user_with_friends: User) -> None:
        """Test that list fields can be modified."""
        original_friends = user_with_friends.friends.copy()
        user_with_friends.friends.append("new_friend")

        assert len(user_with_friends.friends) == len(original_friends) + 1
        assert "new_friend" in user_with_friends.friends


class TestDomainEquality:
    """Test domain equality comparison."""

    def test_same_values_equal(self, user_class: Type[User]) -> None:
        """Test that domains with same values are equal."""
        user1 = user_class(id=1, username="alice", email="alice@example.com")
        user2 = user_class(id=1, username="alice", email="alice@example.com")

        assert user1 == user2

    def test_different_values_not_equal(self, user_class: Type[User]) -> None:
        """Test that domains with different values are not equal."""
        user1 = user_class(id=1, username="alice", email="alice@example.com")
        user2 = user_class(id=2, username="bob", email="bob@example.com")

        assert user1 != user2

    def test_different_optional_fields_not_equal(self, user_class: Type[User]) -> None:
        """Test that different optional fields affect equality."""
        user1 = user_class(
            id=1, username="alice", email="alice@example.com", tutor="bob"
        )
        user2 = user_class(id=1, username="alice", email="alice@example.com")

        assert user1 != user2


class TestComplexDomainStructures:
    """Test complex domain structures."""

    def test_nested_lists(self, user_class: Type[User]) -> None:
        """Test that complex list structures work."""
        user = user_class(
            id=1,
            username="test",
            email="test@example.com",
            friends=["friend1", "friend2", "friend3", "friend4", "friend5"],
        )

        assert len(user.friends) == 5
        assert "friend3" in user.friends

    def test_unicode_strings(self, user_class: Type[User]) -> None:
        """Test that unicode strings are handled correctly."""
        user = user_class(id=1, username="用户名", email="test@例え.jp")

        assert user.username == "用户名"
        assert "例え" in user.email

    def test_long_strings(self, user_class: Type[User]) -> None:
        """Test that long strings are handled correctly."""
        long_username = "a" * 1000
        user = user_class(id=1, username=long_username, email="test@example.com")

        assert len(user.username) == 1000
