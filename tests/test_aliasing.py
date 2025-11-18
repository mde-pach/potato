"""Tests for domain aliasing functionality."""

from __future__ import annotations

from typing import Annotated

import pytest
from pydantic import ValidationError

from potato.domain.aggregates import Aggregate
from potato.dto import ViewDTO

from .conftest import Buyer, Product, Seller

# =============================================================================
# Aliased ViewDTO Test Classes
# =============================================================================


class OrderView(ViewDTO[Aggregate[Buyer, Seller, Product]]):
    """ViewDTO with aliased domains for buyer and seller."""

    buyer_id: Annotated[int, Buyer.id]
    buyer_username: Annotated[str, Buyer.username]
    buyer_email: Annotated[str, Buyer.email]

    seller_id: Annotated[int, Seller.id]
    seller_username: Annotated[str, Seller.username]

    product_id: Annotated[int, Product.id]
    product_name: Annotated[str, Product.name]
    product_description: Annotated[str, Product.description]


class SimpleAliasedView(ViewDTO[Aggregate[Buyer, Seller]]):
    """Simple ViewDTO with just buyer and seller."""

    buyer_id: Annotated[int, Buyer.id]
    buyer_name: Annotated[str, Buyer.username]
    seller_id: Annotated[int, Seller.id]
    seller_name: Annotated[str, Seller.username]


class PartialAliasedView(ViewDTO[Aggregate[Buyer, Seller, Product]]):
    """ViewDTO that only includes some fields from aliased domains."""

    buyer_id: Annotated[int, Buyer.id]
    seller_id: Annotated[int, Seller.id]
    product_name: Annotated[str, Product.name]


# =============================================================================
# Test Aliased ViewDTO Creation
# =============================================================================


class TestAliasedViewDTOCreation:
    """Test creating ViewDTOs with aliased domains."""

    def test_build_with_named_arguments(self, buyer_user, seller_user, laptop_product):
        """Test building ViewDTO with named arguments for aliases."""
        view = OrderView.build(
            buyer=buyer_user, seller=seller_user, product=laptop_product
        )

        assert view.buyer_id == 10
        assert view.buyer_username == "buyer1"
        assert view.buyer_email == "buyer1@example.com"
        assert view.seller_id == 20
        assert view.seller_username == "seller1"
        assert view.product_id == 100
        assert view.product_name == "Laptop"

    def test_build_simple_aliased_view(self, buyer_user, seller_user):
        """Test building simple ViewDTO with just two aliases."""
        view = SimpleAliasedView.build(buyer=buyer_user, seller=seller_user)

        assert view.buyer_id == 10
        assert view.buyer_name == "buyer1"
        assert view.seller_id == 20
        assert view.seller_name == "seller1"

    def test_build_partial_aliased_view(
        self, buyer_user, seller_user, smartphone_product
    ):
        """Test building ViewDTO with partial field selection."""
        view = PartialAliasedView.build(
            buyer=buyer_user, seller=seller_user, product=smartphone_product
        )

        assert view.buyer_id == 10
        assert view.seller_id == 20
        assert view.product_name == "Smartphone"
        # Other fields not included in view
        assert not hasattr(view, "buyer_username")
        assert not hasattr(view, "seller_username")


class TestAliasedViewDTOFieldMapping:
    """Test field mapping with aliased domains."""

    def test_buyer_fields_mapped_correctly(
        self, buyer_user, seller_user, simple_product
    ):
        """Test that buyer fields are mapped correctly."""
        view = OrderView.build(
            buyer=buyer_user, seller=seller_user, product=simple_product
        )

        # All buyer fields should map to buyer instance
        assert view.buyer_id == buyer_user.id
        assert view.buyer_username == buyer_user.username
        assert view.buyer_email == buyer_user.email

    def test_seller_fields_mapped_correctly(
        self, buyer_user, seller_user, simple_product
    ):
        """Test that seller fields are mapped correctly."""
        view = OrderView.build(
            buyer=buyer_user, seller=seller_user, product=simple_product
        )

        # All seller fields should map to seller instance
        assert view.seller_id == seller_user.id
        assert view.seller_username == seller_user.username

    def test_different_users_mapped_to_different_aliases(
        self, simple_user, complete_user, simple_product
    ):
        """Test that different user instances are correctly distinguished."""
        view = OrderView.build(
            buyer=simple_user, seller=complete_user, product=simple_product
        )

        # Verify they're different users
        assert view.buyer_id != view.seller_id
        assert view.buyer_username != view.seller_username
        assert view.buyer_username == "alice"
        assert view.seller_username == "diana"


class TestAliasedViewDTOSerialization:
    """Test serialization of aliased ViewDTOs."""

    def test_model_dump(self, buyer_user, seller_user, laptop_product):
        """Test model_dump with aliased ViewDTO."""
        view = OrderView.build(
            buyer=buyer_user, seller=seller_user, product=laptop_product
        )
        data = view.model_dump()

        assert data["buyer_id"] == 10
        assert data["buyer_username"] == "buyer1"
        assert data["seller_id"] == 20
        assert data["seller_username"] == "seller1"
        assert data["product_name"] == "Laptop"

    def test_model_dump_json(self, buyer_user, seller_user, simple_product):
        """Test JSON serialization."""
        view = OrderView.build(
            buyer=buyer_user, seller=seller_user, product=simple_product
        )
        json_str = view.model_dump_json()

        assert isinstance(json_str, str)
        assert "buyer1" in json_str
        assert "seller1" in json_str
        assert "Widget" in json_str


class TestAliasedViewDTOImmutability:
    """Test immutability of aliased ViewDTOs."""

    def test_view_is_frozen(self, buyer_user, seller_user, simple_product):
        """Test that aliased ViewDTO is frozen."""
        view = OrderView.build(
            buyer=buyer_user, seller=seller_user, product=simple_product
        )

        with pytest.raises((AttributeError, ValidationError)):
            view.buyer_id = 999

    def test_cannot_modify_any_field(self, buyer_user, seller_user, simple_product):
        """Test that no field can be modified."""
        view = OrderView.build(
            buyer=buyer_user, seller=seller_user, product=simple_product
        )

        with pytest.raises((AttributeError, ValidationError)):
            view.seller_username = "hacker"


class TestAliasedViewDTOErrorHandling:
    """Test error handling with aliased ViewDTOs."""

    def test_missing_required_alias_raises_error(self, buyer_user, simple_product):
        """Test that missing required aliased argument raises error."""
        # Missing seller argument
        with pytest.raises((ValueError, TypeError, KeyError)):
            OrderView.build(buyer=buyer_user, product=simple_product)

    def test_wrong_argument_name_raises_error(
        self, buyer_user, seller_user, simple_product
    ):
        """Test that wrong argument names are handled."""
        # Using 'customer' instead of 'buyer'
        with pytest.raises((ValueError, TypeError)):
            OrderView.build(
                customer=buyer_user, seller=seller_user, product=simple_product
            )


class TestAliasedViewDTOComplexScenarios:
    """Test complex scenarios with aliased ViewDTOs."""

    def test_same_user_as_buyer_and_seller(self, simple_user, simple_product):
        """Test using same user instance for both buyer and seller."""
        view = OrderView.build(
            buyer=simple_user, seller=simple_user, product=simple_product
        )

        # Should work, but fields should be same
        assert view.buyer_id == view.seller_id
        assert view.buyer_username == view.seller_username
        assert view.buyer_id == 1

    def test_multiple_views_from_same_data(
        self, buyer_user, seller_user, simple_product
    ):
        """Test creating multiple views from same data."""
        view1 = OrderView.build(
            buyer=buyer_user, seller=seller_user, product=simple_product
        )
        view2 = OrderView.build(
            buyer=buyer_user, seller=seller_user, product=simple_product
        )

        assert view1 == view2

    def test_swapped_buyer_and_seller(self, buyer_user, seller_user, simple_product):
        """Test swapping buyer and seller arguments."""
        view1 = OrderView.build(
            buyer=buyer_user, seller=seller_user, product=simple_product
        )
        view2 = OrderView.build(
            buyer=seller_user,  # Swapped
            seller=buyer_user,  # Swapped
            product=simple_product,
        )

        # Views should have swapped IDs
        assert view1.buyer_id == view2.seller_id
        assert view1.seller_id == view2.buyer_id


class TestAliasDefinitions:
    """Test alias definition and usage."""

    def test_buyer_alias_is_distinct_type(self, buyer_alias, user_class):
        """Test that Buyer alias is treated as distinct type."""
        # Buyer and User are related but distinct for typing purposes
        assert buyer_alias is not user_class

    def test_seller_alias_is_distinct_type(self, seller_alias, user_class):
        """Test that Seller alias is treated as distinct type."""
        assert seller_alias is not user_class

    def test_buyer_and_seller_are_different(self, buyer_alias, seller_alias):
        """Test that Buyer and Seller aliases are different."""
        assert buyer_alias is not seller_alias
