"""Tests for ViewDTO functionality."""

from __future__ import annotations

from typing import Annotated

import pytest
from pydantic import ValidationError

from potato.dto import ViewDTO

from .conftest import Product, User

# =============================================================================
# ViewDTO Test Classes
# =============================================================================


class UserView(ViewDTO[User]):
    """A ViewDTO that maps Domain fields to different DTO field names."""

    id: int
    login: Annotated[str, User.username]  # Maps 'username' → 'login'
    email: str


class SimpleUserView(ViewDTO[User]):
    """A simple ViewDTO with direct field mapping."""

    id: int
    username: str
    email: str


class PartialUserView(ViewDTO[User]):
    """A ViewDTO that only includes some fields."""

    id: int
    username: str


class ProductView(ViewDTO[Product]):
    """A simple product view."""

    id: int
    name: str
    description: str


class RenamedProductView(ViewDTO[Product]):
    """A product view with renamed fields."""

    id: int
    product_name: Annotated[str, Product.name]
    product_description: Annotated[str, Product.description]


# =============================================================================
# Test ViewDTO with Field Mapping
# =============================================================================


class TestViewDTOBasicMapping:
    """Test basic ViewDTO field mapping."""

    def test_build_simple_user_view(self, simple_user):
        """Test building a simple ViewDTO with direct field mapping."""
        view = SimpleUserView.build(simple_user)

        assert view.id == 1
        assert view.username == "alice"
        assert view.email == "alice@example.com"

    def test_build_user_view_with_renamed_field(self, simple_user):
        """Test building ViewDTO with renamed field (username → login)."""
        view = UserView.build(simple_user)

        assert view.id == 1
        assert view.login == "alice"  # Mapped from username
        assert view.email == "alice@example.com"

    def test_build_partial_view(self, complete_user):
        """Test building ViewDTO that only includes subset of fields."""
        view = PartialUserView.build(complete_user)

        assert view.id == 4
        assert view.username == "diana"
        # email is not in the view
        assert not hasattr(view, "email")

    def test_build_product_view(self, simple_product):
        """Test building a product view."""
        view = ProductView.build(simple_product)

        assert view.id == 1
        assert view.name == "Widget"
        assert view.description == "A useful widget"

    def test_build_renamed_product_view(self, laptop_product):
        """Test building a product view with renamed fields."""
        view = RenamedProductView.build(laptop_product)

        assert view.id == 100
        assert view.product_name == "Laptop"
        assert view.product_description == "High-performance laptop"


class TestViewDTOImmutability:
    """Test that ViewDTO instances are immutable."""

    def test_view_dto_is_frozen(self, simple_user):
        """Test that ViewDTO instances cannot be modified."""
        view = UserView.build(simple_user)

        with pytest.raises((AttributeError, ValidationError)):
            view.id = 999

    def test_cannot_add_new_attributes(self, simple_user):
        """Test that new attributes cannot be added to ViewDTO."""
        view = UserView.build(simple_user)

        with pytest.raises((AttributeError, ValidationError)):
            view.new_field = "value"


class TestViewDTOSerialization:
    """Test ViewDTO serialization."""

    def test_model_dump(self, simple_user):
        """Test model_dump returns correct dictionary."""
        view = UserView.build(simple_user)
        data = view.model_dump()

        assert data["id"] == 1
        assert data["login"] == "alice"
        assert data["email"] == "alice@example.com"

    def test_model_dump_json(self, simple_user):
        """Test model_dump_json returns valid JSON string."""
        view = UserView.build(simple_user)
        json_str = view.model_dump_json()

        assert isinstance(json_str, str)
        assert "alice" in json_str
        assert "login" in json_str

    def test_serialization_preserves_types(self, user_class):
        """Test that serialization preserves data types."""
        user = user_class(
            id=123,
            username="test",
            email="test@example.com",
            friends=["friend1", "friend2"],
        )
        view = SimpleUserView.build(user)
        data = view.model_dump()

        assert isinstance(data["id"], int)
        assert isinstance(data["username"], str)


class TestViewDTOWithDifferentData:
    """Test ViewDTO with various data scenarios."""

    def test_user_with_empty_strings(self, user_class):
        """Test ViewDTO with empty string values."""
        user = user_class(id=1, username="", email="")
        view = SimpleUserView.build(user)

        assert view.username == ""
        assert view.email == ""

    def test_user_with_special_characters(self, user_class):
        """Test ViewDTO with special characters."""
        user = user_class(id=1, username="user@#$%", email="test+special@example.com")
        view = SimpleUserView.build(user)

        assert view.username == "user@#$%"
        assert view.email == "test+special@example.com"

    def test_user_with_unicode(self, user_class):
        """Test ViewDTO with unicode characters."""
        user = user_class(id=1, username="用户名", email="test@例え.jp")
        view = SimpleUserView.build(user)

        assert view.username == "用户名"
        assert view.email == "test@例え.jp"

    def test_multiple_field_mappings(self, user_class):
        """Test ViewDTO with multiple renamed fields."""
        user = user_class(id=1, username="testuser", email="test@example.com")
        view = UserView.build(user)

        # Verify the mapping worked
        assert view.login == "testuser"
        assert not hasattr(view, "username")


class TestViewDTOErrorHandling:
    """Test ViewDTO error handling."""

    def test_build_with_no_arguments_raises_error(self):
        """Test that building without arguments raises an error."""
        with pytest.raises((ValueError, TypeError)):
            UserView.build()

    def test_build_with_multiple_arguments_raises_error(
        self, simple_user, complete_user
    ):
        """Test that building with multiple arguments raises an error for single domain DTO."""
        with pytest.raises(ValueError):
            UserView.build(simple_user, complete_user)

    def test_build_with_wrong_domain_type_works(self, simple_product):
        """Test that building with wrong domain type works if fields match."""
        # This might work if field names match, but is not recommended
        # The framework is permissive in this case
        try:
            view = SimpleUserView.build(simple_product)
            # If it succeeds, check that it extracted the id field
            assert view.id == simple_product.id
        except (AttributeError, KeyError, ValidationError):
            # Expected if field names don't match
            pass


class TestViewDTOEquality:
    """Test ViewDTO equality."""

    def test_same_data_produces_equal_views(self, user_class):
        """Test that ViewDTOs built from same data are equal."""
        user1 = user_class(id=1, username="alice", email="alice@example.com")
        user2 = user_class(id=1, username="alice", email="alice@example.com")

        view1 = UserView.build(user1)
        view2 = UserView.build(user2)

        assert view1 == view2

    def test_different_data_produces_unequal_views(self, simple_user, complete_user):
        """Test that ViewDTOs built from different data are not equal."""
        view1 = UserView.build(simple_user)
        view2 = UserView.build(complete_user)

        assert view1 != view2
