"""Tests for Domain aggregates with aliasing."""

from __future__ import annotations

from typing import Annotated

import pytest
from pydantic import ValidationError

from potato.domain import Domain
from potato.domain.aggregates import Aggregate

from .conftest import Buyer, Product, Seller

# =============================================================================
# Domain Aggregate Test Classes with Aliasing
# =============================================================================


class Transaction(Aggregate[Buyer, Seller, Product]):
    """A Domain aggregate with multiple instances of the same domain type."""

    buyer_id: Annotated[int, Buyer.id]
    buyer_name: Annotated[str, Buyer.username]

    seller_id: Annotated[int, Seller.id]
    seller_name: Annotated[str, Seller.username]

    product: Product
    transaction_amount: int


class SimpleTransaction(Aggregate[Buyer, Seller]):
    """Simple transaction with just buyer and seller."""

    buyer_id: Annotated[int, Buyer.id]
    seller_id: Annotated[int, Seller.id]
    amount: int


class DetailedTransaction(Aggregate[Buyer, Seller, Product]):
    """Detailed transaction with more fields."""

    buyer_id: Annotated[int, Buyer.id]
    buyer_name: Annotated[str, Buyer.username]
    buyer_email: Annotated[str, Buyer.email]

    seller_id: Annotated[int, Seller.id]
    seller_name: Annotated[str, Seller.username]
    seller_email: Annotated[str, Seller.email]

    product_id: Annotated[int, Product.id]
    product_name: Annotated[str, Product.name]

    transaction_amount: int
    transaction_date: str = ""


# =============================================================================
# Test Domain Aggregate Creation with Aliasing
# =============================================================================


class TestDomainAggregateWithAliasingCreation:
    """Test creating domain aggregates with aliased types."""

    def test_create_basic_transaction(
        self, buyer_user, seller_user, smartphone_product
    ):
        """Test creating a basic transaction."""
        transaction = Transaction(
            buyer_id=buyer_user.id,
            buyer_name=buyer_user.username,
            seller_id=seller_user.id,
            seller_name=seller_user.username,
            product=smartphone_product,
            transaction_amount=999,
        )

        assert transaction.buyer_id == 10
        assert transaction.buyer_name == "buyer1"
        assert transaction.seller_id == 20
        assert transaction.seller_name == "seller1"
        assert transaction.product.name == "Smartphone"
        assert transaction.transaction_amount == 999

    def test_create_simple_transaction(self, buyer_user, seller_user):
        """Test creating simple transaction without product."""
        transaction = SimpleTransaction(
            buyer_id=buyer_user.id, seller_id=seller_user.id, amount=500
        )

        assert transaction.buyer_id == 10
        assert transaction.seller_id == 20
        assert transaction.amount == 500

    def test_create_detailed_transaction(self, buyer_user, seller_user, laptop_product):
        """Test creating detailed transaction with all fields."""
        transaction = DetailedTransaction(
            buyer_id=buyer_user.id,
            buyer_name=buyer_user.username,
            buyer_email=buyer_user.email,
            seller_id=seller_user.id,
            seller_name=seller_user.username,
            seller_email=seller_user.email,
            product_id=laptop_product.id,
            product_name=laptop_product.name,
            transaction_amount=1500,
            transaction_date="2025-01-15",
        )

        assert transaction.buyer_email == "buyer1@example.com"
        assert transaction.seller_email == "seller1@example.com"
        assert transaction.product_id == 100
        assert transaction.product_name == "Laptop"
        assert transaction.transaction_date == "2025-01-15"


class TestDomainAggregateWithAliasingAccess:
    """Test accessing fields in aliased domain aggregates."""

    def test_access_buyer_fields(self, buyer_user, seller_user, simple_product):
        """Test accessing buyer-related fields."""
        transaction = Transaction(
            buyer_id=buyer_user.id,
            buyer_name=buyer_user.username,
            seller_id=seller_user.id,
            seller_name=seller_user.username,
            product=simple_product,
            transaction_amount=100,
        )

        assert transaction.buyer_id == 10
        assert transaction.buyer_name == "buyer1"

    def test_access_seller_fields(self, buyer_user, seller_user, simple_product):
        """Test accessing seller-related fields."""
        transaction = Transaction(
            buyer_id=buyer_user.id,
            buyer_name=buyer_user.username,
            seller_id=seller_user.id,
            seller_name=seller_user.username,
            product=simple_product,
            transaction_amount=100,
        )

        assert transaction.seller_id == 20
        assert transaction.seller_name == "seller1"

    def test_access_nested_product_fields(
        self, buyer_user, seller_user, laptop_product
    ):
        """Test accessing nested product domain fields."""
        transaction = Transaction(
            buyer_id=buyer_user.id,
            buyer_name=buyer_user.username,
            seller_id=seller_user.id,
            seller_name=seller_user.username,
            product=laptop_product,
            transaction_amount=1500,
        )

        assert transaction.product.id == 100
        assert transaction.product.name == "Laptop"
        assert transaction.product.description == "High-performance laptop"

    def test_modify_transaction_fields(self, buyer_user, seller_user, simple_product):
        """Test modifying transaction fields."""
        transaction = Transaction(
            buyer_id=buyer_user.id,
            buyer_name=buyer_user.username,
            seller_id=seller_user.id,
            seller_name=seller_user.username,
            product=simple_product,
            transaction_amount=100,
        )

        transaction.transaction_amount = 200
        assert transaction.transaction_amount == 200


class TestDomainAggregateWithAliasingSerialization:
    """Test serialization of aliased domain aggregates."""

    def test_model_dump(self, buyer_user, seller_user, smartphone_product):
        """Test model_dump includes all fields."""
        transaction = Transaction(
            buyer_id=buyer_user.id,
            buyer_name=buyer_user.username,
            seller_id=seller_user.id,
            seller_name=seller_user.username,
            product=smartphone_product,
            transaction_amount=999,
        )
        data = transaction.model_dump()

        assert data["buyer_id"] == 10
        assert data["buyer_name"] == "buyer1"
        assert data["seller_id"] == 20
        assert data["seller_name"] == "seller1"
        assert data["product"]["name"] == "Smartphone"
        assert data["transaction_amount"] == 999

    def test_model_dump_json(self, buyer_user, seller_user, simple_product):
        """Test JSON serialization."""
        transaction = Transaction(
            buyer_id=buyer_user.id,
            buyer_name=buyer_user.username,
            seller_id=seller_user.id,
            seller_name=seller_user.username,
            product=simple_product,
            transaction_amount=100,
        )
        json_str = transaction.model_dump_json()

        assert isinstance(json_str, str)
        assert "buyer1" in json_str
        assert "seller1" in json_str
        assert "Widget" in json_str

    def test_model_dump_exclude(self, buyer_user, seller_user, simple_product):
        """Test model_dump with exclude option."""
        transaction = Transaction(
            buyer_id=buyer_user.id,
            buyer_name=buyer_user.username,
            seller_id=seller_user.id,
            seller_name=seller_user.username,
            product=simple_product,
            transaction_amount=100,
        )
        data = transaction.model_dump(exclude={"product"})

        assert "buyer_id" in data
        assert "seller_id" in data
        assert "product" not in data


class TestDomainAggregateWithAliasingValidation:
    """Test validation of aliased domain aggregates."""

    def test_missing_buyer_field_raises_error(self, seller_user, simple_product):
        """Test that missing buyer field raises error."""
        with pytest.raises(ValidationError):
            Transaction(
                # Missing buyer_id and buyer_name
                seller_id=seller_user.id,
                seller_name=seller_user.username,
                product=simple_product,
                transaction_amount=100,
            )

    def test_missing_seller_field_raises_error(self, buyer_user, simple_product):
        """Test that missing seller field raises error."""
        with pytest.raises(ValidationError):
            Transaction(
                buyer_id=buyer_user.id,
                buyer_name=buyer_user.username,
                # Missing seller_id and seller_name
                product=simple_product,
                transaction_amount=100,
            )

    def test_missing_product_raises_error(self, buyer_user, seller_user):
        """Test that missing product raises error."""
        with pytest.raises(ValidationError):
            Transaction(
                buyer_id=buyer_user.id,
                buyer_name=buyer_user.username,
                seller_id=seller_user.id,
                seller_name=seller_user.username,
                # Missing product
                transaction_amount=100,
            )

    def test_invalid_type_for_extracted_field(
        self, buyer_user, seller_user, simple_product
    ):
        """Test that invalid type for extracted field raises error."""
        with pytest.raises(ValidationError):
            Transaction(
                buyer_id="not_an_int",  # Should be int
                buyer_name=buyer_user.username,
                seller_id=seller_user.id,
                seller_name=seller_user.username,
                product=simple_product,
                transaction_amount=100,
            )


class TestDomainAggregateWithAliasingEquality:
    """Test equality of aliased domain aggregates."""

    def test_same_data_equal(self, buyer_user, seller_user, simple_product):
        """Test that transactions with same data are equal."""
        transaction1 = Transaction(
            buyer_id=buyer_user.id,
            buyer_name=buyer_user.username,
            seller_id=seller_user.id,
            seller_name=seller_user.username,
            product=simple_product,
            transaction_amount=100,
        )
        transaction2 = Transaction(
            buyer_id=buyer_user.id,
            buyer_name=buyer_user.username,
            seller_id=seller_user.id,
            seller_name=seller_user.username,
            product=simple_product,
            transaction_amount=100,
        )

        assert transaction1 == transaction2

    def test_different_amount_not_equal(self, buyer_user, seller_user, simple_product):
        """Test that different amounts make transactions unequal."""
        transaction1 = Transaction(
            buyer_id=buyer_user.id,
            buyer_name=buyer_user.username,
            seller_id=seller_user.id,
            seller_name=seller_user.username,
            product=simple_product,
            transaction_amount=100,
        )
        transaction2 = Transaction(
            buyer_id=buyer_user.id,
            buyer_name=buyer_user.username,
            seller_id=seller_user.id,
            seller_name=seller_user.username,
            product=simple_product,
            transaction_amount=200,
        )

        assert transaction1 != transaction2

    def test_different_product_not_equal(
        self, buyer_user, seller_user, simple_product, laptop_product
    ):
        """Test that different products make transactions unequal."""
        transaction1 = Transaction(
            buyer_id=buyer_user.id,
            buyer_name=buyer_user.username,
            seller_id=seller_user.id,
            seller_name=seller_user.username,
            product=simple_product,
            transaction_amount=100,
        )
        transaction2 = Transaction(
            buyer_id=buyer_user.id,
            buyer_name=buyer_user.username,
            seller_id=seller_user.id,
            seller_name=seller_user.username,
            product=laptop_product,
            transaction_amount=100,
        )

        assert transaction1 != transaction2


class TestDomainAggregateComplexScenarios:
    """Test complex scenarios with aliased domain aggregates."""

    def test_same_user_as_buyer_and_seller(self, simple_user, simple_product):
        """Test transaction where buyer and seller are same user."""
        transaction = Transaction(
            buyer_id=simple_user.id,
            buyer_name=simple_user.username,
            seller_id=simple_user.id,
            seller_name=simple_user.username,
            product=simple_product,
            transaction_amount=0,  # Self-transaction
        )

        assert transaction.buyer_id == transaction.seller_id
        assert transaction.buyer_name == transaction.seller_name

    def test_zero_amount_transaction(self, buyer_user, seller_user, simple_product):
        """Test transaction with zero amount."""
        transaction = Transaction(
            buyer_id=buyer_user.id,
            buyer_name=buyer_user.username,
            seller_id=seller_user.id,
            seller_name=seller_user.username,
            product=simple_product,
            transaction_amount=0,
        )

        assert transaction.transaction_amount == 0

    def test_negative_amount_allowed(self, buyer_user, seller_user, simple_product):
        """Test that negative amounts are allowed (refund scenario)."""
        transaction = Transaction(
            buyer_id=buyer_user.id,
            buyer_name=buyer_user.username,
            seller_id=seller_user.id,
            seller_name=seller_user.username,
            product=simple_product,
            transaction_amount=-50,
        )

        assert transaction.transaction_amount == -50

    def test_large_transaction_amount(self, buyer_user, seller_user, laptop_product):
        """Test transaction with very large amount."""
        transaction = Transaction(
            buyer_id=buyer_user.id,
            buyer_name=buyer_user.username,
            seller_id=seller_user.id,
            seller_name=seller_user.username,
            product=laptop_product,
            transaction_amount=999999999,
        )

        assert transaction.transaction_amount == 999999999

    def test_detailed_transaction_with_optional_fields(
        self, buyer_user, seller_user, simple_product
    ):
        """Test detailed transaction with and without optional fields."""
        # Without optional field
        transaction1 = DetailedTransaction(
            buyer_id=buyer_user.id,
            buyer_name=buyer_user.username,
            buyer_email=buyer_user.email,
            seller_id=seller_user.id,
            seller_name=seller_user.username,
            seller_email=seller_user.email,
            product_id=simple_product.id,
            product_name=simple_product.name,
            transaction_amount=100,
        )
        assert transaction1.transaction_date == ""

        # With optional field
        transaction2 = DetailedTransaction(
            buyer_id=buyer_user.id,
            buyer_name=buyer_user.username,
            buyer_email=buyer_user.email,
            seller_id=seller_user.id,
            seller_name=seller_user.username,
            seller_email=seller_user.email,
            product_id=simple_product.id,
            product_name=simple_product.name,
            transaction_amount=100,
            transaction_date="2025-01-20",
        )
        assert transaction2.transaction_date == "2025-01-20"
