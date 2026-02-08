"""Tests for ViewDTO with Aggregate domains (replaces old aliasing tests).

In the new API, there are no aliases. Aggregate field names serve as namespaces.
ViewDTOs for aggregates use Field(source=Aggregate.field.subfield) to map nested fields.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from potato import Field
from potato.domain import Aggregate
from potato.dto import ViewDTO

from ..fixtures.domains import Product, User


# =============================================================================
# Aggregate + ViewDTO Test Classes
# =============================================================================


class OrderAggregate(Aggregate):
    """Aggregate with buyer, seller, and product."""
    buyer: User
    seller: User
    product: Product


class OrderView(ViewDTO[OrderAggregate]):
    """ViewDTO with mapped fields from aggregate."""

    buyer_id: int = Field(source=OrderAggregate.buyer.id)
    buyer_username: str = Field(source=OrderAggregate.buyer.username)
    buyer_email: str = Field(source=OrderAggregate.buyer.email)

    seller_id: int = Field(source=OrderAggregate.seller.id)
    seller_username: str = Field(source=OrderAggregate.seller.username)

    product_id: int = Field(source=OrderAggregate.product.id)
    product_name: str = Field(source=OrderAggregate.product.name)
    product_description: str = Field(source=OrderAggregate.product.description)


class RelationAggregate(Aggregate):
    """Simple aggregate with buyer and seller."""
    buyer: User
    seller: User


class SimpleAliasedView(ViewDTO[RelationAggregate]):
    """Simple ViewDTO with just buyer and seller."""

    buyer_id: int = Field(source=RelationAggregate.buyer.id)
    buyer_name: str = Field(source=RelationAggregate.buyer.username)
    seller_id: int = Field(source=RelationAggregate.seller.id)
    seller_name: str = Field(source=RelationAggregate.seller.username)


class PartialAliasedView(ViewDTO[OrderAggregate]):
    """ViewDTO that only includes some fields from aggregate."""

    buyer_id: int = Field(source=OrderAggregate.buyer.id)
    seller_id: int = Field(source=OrderAggregate.seller.id)
    product_name: str = Field(source=OrderAggregate.product.name)


# =============================================================================
# Test Aggregate ViewDTO Creation
# =============================================================================


class TestAggregateViewDTOCreation:
    """Test creating ViewDTOs from aggregates."""

    def test_build_order_view(
        self, buyer_user: User, seller_user: User, laptop_product: Product
    ) -> None:
        """Test building ViewDTO from aggregate."""
        aggregate = OrderAggregate(buyer=buyer_user, seller=seller_user, product=laptop_product)
        view = OrderView.from_domain(aggregate)

        assert view.buyer_id == 10
        assert view.buyer_username == "buyer1"
        assert view.buyer_email == "buyer1@example.com"
        assert view.seller_id == 20
        assert view.seller_username == "seller1"
        assert view.product_id == 100
        assert view.product_name == "Laptop"

    def test_build_simple_view(
        self, buyer_user: User, seller_user: User
    ) -> None:
        """Test building simple ViewDTO with just two domains."""
        aggregate = RelationAggregate(buyer=buyer_user, seller=seller_user)
        view = SimpleAliasedView.from_domain(aggregate)

        assert view.buyer_id == 10
        assert view.buyer_name == "buyer1"
        assert view.seller_id == 20
        assert view.seller_name == "seller1"

    def test_build_partial_view(
        self, buyer_user: User, seller_user: User, smartphone_product: Product
    ) -> None:
        """Test building ViewDTO with partial field selection."""
        aggregate = OrderAggregate(buyer=buyer_user, seller=seller_user, product=smartphone_product)
        view = PartialAliasedView.from_domain(aggregate)

        assert view.buyer_id == 10
        assert view.seller_id == 20
        assert view.product_name == "Smartphone"
        assert not hasattr(view, "buyer_username")
        assert not hasattr(view, "seller_username")


class TestAggregateViewDTOFieldMapping:
    """Test field mapping with aggregate domains."""

    def test_buyer_fields_mapped_correctly(
        self, buyer_user: User, seller_user: User, simple_product: Product
    ) -> None:
        """Test that buyer fields are mapped correctly."""
        aggregate = OrderAggregate(buyer=buyer_user, seller=seller_user, product=simple_product)
        view = OrderView.from_domain(aggregate)

        assert view.buyer_id == buyer_user.id
        assert view.buyer_username == buyer_user.username
        assert view.buyer_email == buyer_user.email

    def test_seller_fields_mapped_correctly(
        self, buyer_user: User, seller_user: User, simple_product: Product
    ) -> None:
        """Test that seller fields are mapped correctly."""
        aggregate = OrderAggregate(buyer=buyer_user, seller=seller_user, product=simple_product)
        view = OrderView.from_domain(aggregate)

        assert view.seller_id == seller_user.id
        assert view.seller_username == seller_user.username

    def test_different_users_mapped_to_different_fields(
        self, simple_user: User, complete_user: User, simple_product: Product
    ) -> None:
        """Test that different user instances are correctly distinguished."""
        aggregate = OrderAggregate(buyer=simple_user, seller=complete_user, product=simple_product)
        view = OrderView.from_domain(aggregate)

        assert view.buyer_id != view.seller_id
        assert view.buyer_username != view.seller_username
        assert view.buyer_username == "alice"
        assert view.seller_username == "diana"


class TestAggregateViewDTOSerialization:
    """Test serialization of aggregate ViewDTOs."""

    def test_model_dump(
        self, buyer_user: User, seller_user: User, laptop_product: Product
    ) -> None:
        """Test model_dump with aggregate ViewDTO."""
        aggregate = OrderAggregate(buyer=buyer_user, seller=seller_user, product=laptop_product)
        view = OrderView.from_domain(aggregate)
        data = view.model_dump()

        assert data["buyer_id"] == 10
        assert data["buyer_username"] == "buyer1"
        assert data["seller_id"] == 20
        assert data["seller_username"] == "seller1"
        assert data["product_name"] == "Laptop"

    def test_model_dump_json(
        self, buyer_user: User, seller_user: User, simple_product: Product
    ) -> None:
        """Test JSON serialization."""
        aggregate = OrderAggregate(buyer=buyer_user, seller=seller_user, product=simple_product)
        view = OrderView.from_domain(aggregate)
        json_str = view.model_dump_json()

        assert isinstance(json_str, str)
        assert "buyer1" in json_str
        assert "seller1" in json_str
        assert "Widget" in json_str


class TestAggregateViewDTOImmutability:
    """Test immutability of aggregate ViewDTOs."""

    def test_view_is_frozen(
        self, buyer_user: User, seller_user: User, simple_product: Product
    ) -> None:
        """Test that aggregate ViewDTO is frozen."""
        aggregate = OrderAggregate(buyer=buyer_user, seller=seller_user, product=simple_product)
        view = OrderView.from_domain(aggregate)

        with pytest.raises((AttributeError, ValidationError)):
            view.buyer_id = 999

    def test_cannot_modify_any_field(
        self, buyer_user: User, seller_user: User, simple_product: Product
    ) -> None:
        """Test that no field can be modified."""
        aggregate = OrderAggregate(buyer=buyer_user, seller=seller_user, product=simple_product)
        view = OrderView.from_domain(aggregate)

        with pytest.raises((AttributeError, ValidationError)):
            view.seller_username = "hacker"


class TestAggregateViewDTOComplexScenarios:
    """Test complex scenarios with aggregate ViewDTOs."""

    def test_same_user_as_buyer_and_seller(
        self, simple_user: User, simple_product: Product
    ) -> None:
        """Test using same user instance for both buyer and seller."""
        aggregate = OrderAggregate(buyer=simple_user, seller=simple_user, product=simple_product)
        view = OrderView.from_domain(aggregate)

        assert view.buyer_id == view.seller_id
        assert view.buyer_username == view.seller_username
        assert view.buyer_id == 1

    def test_multiple_views_from_same_data(
        self, buyer_user: User, seller_user: User, simple_product: Product
    ) -> None:
        """Test creating multiple views from same data."""
        aggregate = OrderAggregate(buyer=buyer_user, seller=seller_user, product=simple_product)
        view1 = OrderView.from_domain(aggregate)
        view2 = OrderView.from_domain(aggregate)

        assert view1 == view2

    def test_swapped_buyer_and_seller(
        self, buyer_user: User, seller_user: User, simple_product: Product
    ) -> None:
        """Test swapping buyer and seller."""
        agg1 = OrderAggregate(buyer=buyer_user, seller=seller_user, product=simple_product)
        agg2 = OrderAggregate(buyer=seller_user, seller=buyer_user, product=simple_product)

        view1 = OrderView.from_domain(agg1)
        view2 = OrderView.from_domain(agg2)

        assert view1.buyer_id == view2.seller_id
        assert view1.seller_id == view2.buyer_id
