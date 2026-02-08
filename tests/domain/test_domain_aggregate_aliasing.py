"""Tests for Aggregate domains with multiple instances of the same domain type.

In the new API, aliasing is replaced by field-based aggregates where
the field name serves as the namespace.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from potato.domain.aggregates import Aggregate

from ..fixtures.domains import Product, User


# =============================================================================
# Aggregate Test Classes (field names as namespace, no alias())
# =============================================================================


class Transaction(Aggregate):
    """An aggregate with buyer and seller (both User)."""

    buyer: User
    seller: User
    product: Product
    transaction_amount: int


class SimpleTransaction(Aggregate):
    """Simple transaction with just buyer and seller."""

    buyer: User
    seller: User
    amount: int


class DetailedTransaction(Aggregate):
    """Detailed transaction with more fields."""

    buyer: User
    seller: User
    product: Product
    transaction_amount: int
    transaction_date: str = ""


# =============================================================================
# Test Creation
# =============================================================================


class TestTransactionCreation:
    """Test creating aggregates with multiple instances of the same domain type."""

    def test_create_basic_transaction(
        self, buyer_user: User, seller_user: User, smartphone_product: Product
    ) -> None:
        """Test creating a basic transaction."""
        transaction = Transaction(
            buyer=buyer_user,
            seller=seller_user,
            product=smartphone_product,
            transaction_amount=999,
        )

        assert transaction.buyer.id == 10
        assert transaction.buyer.username == "buyer1"
        assert transaction.seller.id == 20
        assert transaction.seller.username == "seller1"
        assert transaction.product.name == "Smartphone"
        assert transaction.transaction_amount == 999

    def test_create_simple_transaction(
        self, buyer_user: User, seller_user: User
    ) -> None:
        """Test creating simple transaction without product."""
        transaction = SimpleTransaction(
            buyer=buyer_user, seller=seller_user, amount=500
        )

        assert transaction.buyer.id == 10
        assert transaction.seller.id == 20
        assert transaction.amount == 500

    def test_create_detailed_transaction(
        self, buyer_user: User, seller_user: User, laptop_product: Product
    ) -> None:
        """Test creating detailed transaction with all fields."""
        transaction = DetailedTransaction(
            buyer=buyer_user,
            seller=seller_user,
            product=laptop_product,
            transaction_amount=1500,
            transaction_date="2025-01-15",
        )

        assert transaction.buyer.email == "buyer1@example.com"
        assert transaction.seller.email == "seller1@example.com"
        assert transaction.product.id == 100
        assert transaction.product.name == "Laptop"
        assert transaction.transaction_date == "2025-01-15"


# =============================================================================
# Test Access
# =============================================================================


class TestTransactionAccess:
    """Test accessing fields in aggregates with multiple same-type domains."""

    def test_access_buyer_fields(
        self, buyer_user: User, seller_user: User, simple_product: Product
    ) -> None:
        """Test accessing buyer-related fields."""
        transaction = Transaction(
            buyer=buyer_user,
            seller=seller_user,
            product=simple_product,
            transaction_amount=100,
        )

        assert transaction.buyer.id == 10
        assert transaction.buyer.username == "buyer1"

    def test_access_seller_fields(
        self, buyer_user: User, seller_user: User, simple_product: Product
    ) -> None:
        """Test accessing seller-related fields."""
        transaction = Transaction(
            buyer=buyer_user,
            seller=seller_user,
            product=simple_product,
            transaction_amount=100,
        )

        assert transaction.seller.id == 20
        assert transaction.seller.username == "seller1"

    def test_access_nested_product_fields(
        self, buyer_user: User, seller_user: User, laptop_product: Product
    ) -> None:
        """Test accessing nested product domain fields."""
        transaction = Transaction(
            buyer=buyer_user,
            seller=seller_user,
            product=laptop_product,
            transaction_amount=1500,
        )

        assert transaction.product.id == 100
        assert transaction.product.name == "Laptop"
        assert transaction.product.description == "High-performance laptop"

    def test_modify_transaction_fields(
        self, buyer_user: User, seller_user: User, simple_product: Product
    ) -> None:
        """Test modifying transaction fields."""
        transaction = Transaction(
            buyer=buyer_user,
            seller=seller_user,
            product=simple_product,
            transaction_amount=100,
        )

        transaction.transaction_amount = 200
        assert transaction.transaction_amount == 200


# =============================================================================
# Test Serialization
# =============================================================================


class TestTransactionSerialization:
    """Test serialization of aggregates with multiple same-type domains."""

    def test_model_dump(
        self, buyer_user: User, seller_user: User, smartphone_product: Product
    ) -> None:
        """Test model_dump includes all fields."""
        transaction = Transaction(
            buyer=buyer_user,
            seller=seller_user,
            product=smartphone_product,
            transaction_amount=999,
        )
        data = transaction.model_dump()

        assert data["buyer"]["id"] == 10
        assert data["buyer"]["username"] == "buyer1"
        assert data["seller"]["id"] == 20
        assert data["seller"]["username"] == "seller1"
        assert data["product"]["name"] == "Smartphone"
        assert data["transaction_amount"] == 999

    def test_model_dump_json(
        self, buyer_user: User, seller_user: User, simple_product: Product
    ) -> None:
        """Test JSON serialization."""
        transaction = Transaction(
            buyer=buyer_user,
            seller=seller_user,
            product=simple_product,
            transaction_amount=100,
        )
        json_str = transaction.model_dump_json()

        assert isinstance(json_str, str)
        assert "buyer1" in json_str
        assert "seller1" in json_str
        assert "Widget" in json_str

    def test_model_dump_exclude(
        self, buyer_user: User, seller_user: User, simple_product: Product
    ) -> None:
        """Test model_dump with exclude option."""
        transaction = Transaction(
            buyer=buyer_user,
            seller=seller_user,
            product=simple_product,
            transaction_amount=100,
        )
        data = transaction.model_dump(exclude={"product"})

        assert "buyer" in data
        assert "seller" in data
        assert "product" not in data


# =============================================================================
# Test Validation
# =============================================================================


class TestTransactionValidation:
    """Test validation of aggregates with multiple same-type domains."""

    def test_missing_buyer_raises_error(
        self, seller_user: User, simple_product: Product
    ) -> None:
        """Test that missing buyer raises error."""
        with pytest.raises(ValidationError):
            Transaction(
                seller=seller_user,
                product=simple_product,
                transaction_amount=100,
            )

    def test_missing_seller_raises_error(
        self, buyer_user: User, simple_product: Product
    ) -> None:
        """Test that missing seller raises error."""
        with pytest.raises(ValidationError):
            Transaction(
                buyer=buyer_user,
                product=simple_product,
                transaction_amount=100,
            )

    def test_missing_product_raises_error(
        self, buyer_user: User, seller_user: User
    ) -> None:
        """Test that missing product raises error."""
        with pytest.raises(ValidationError):
            Transaction(
                buyer=buyer_user,
                seller=seller_user,
                transaction_amount=100,
            )


# =============================================================================
# Test Equality
# =============================================================================


class TestTransactionEquality:
    """Test equality of aggregates with multiple same-type domains."""

    def test_same_data_equal(
        self, buyer_user: User, seller_user: User, simple_product: Product
    ) -> None:
        """Test that transactions with same data are equal."""
        t1 = Transaction(
            buyer=buyer_user, seller=seller_user, product=simple_product, transaction_amount=100,
        )
        t2 = Transaction(
            buyer=buyer_user, seller=seller_user, product=simple_product, transaction_amount=100,
        )

        assert t1 == t2

    def test_different_amount_not_equal(
        self, buyer_user: User, seller_user: User, simple_product: Product
    ) -> None:
        """Test that different amounts make transactions unequal."""
        t1 = Transaction(
            buyer=buyer_user, seller=seller_user, product=simple_product, transaction_amount=100,
        )
        t2 = Transaction(
            buyer=buyer_user, seller=seller_user, product=simple_product, transaction_amount=200,
        )

        assert t1 != t2

    def test_different_product_not_equal(
        self,
        buyer_user: User,
        seller_user: User,
        simple_product: Product,
        laptop_product: Product,
    ) -> None:
        """Test that different products make transactions unequal."""
        t1 = Transaction(
            buyer=buyer_user, seller=seller_user, product=simple_product, transaction_amount=100,
        )
        t2 = Transaction(
            buyer=buyer_user, seller=seller_user, product=laptop_product, transaction_amount=100,
        )

        assert t1 != t2


# =============================================================================
# Test Complex Scenarios
# =============================================================================


class TestTransactionComplexScenarios:
    """Test complex scenarios with aggregates."""

    def test_same_user_as_buyer_and_seller(
        self, simple_user: User, simple_product: Product
    ) -> None:
        """Test transaction where buyer and seller are same user."""
        transaction = Transaction(
            buyer=simple_user,
            seller=simple_user,
            product=simple_product,
            transaction_amount=0,
        )

        assert transaction.buyer.id == transaction.seller.id
        assert transaction.buyer.username == transaction.seller.username

    def test_zero_amount_transaction(
        self, buyer_user: User, seller_user: User, simple_product: Product
    ) -> None:
        """Test transaction with zero amount."""
        transaction = Transaction(
            buyer=buyer_user,
            seller=seller_user,
            product=simple_product,
            transaction_amount=0,
        )

        assert transaction.transaction_amount == 0

    def test_negative_amount_allowed(
        self, buyer_user: User, seller_user: User, simple_product: Product
    ) -> None:
        """Test that negative amounts are allowed (refund scenario)."""
        transaction = Transaction(
            buyer=buyer_user,
            seller=seller_user,
            product=simple_product,
            transaction_amount=-50,
        )

        assert transaction.transaction_amount == -50

    def test_large_transaction_amount(
        self, buyer_user: User, seller_user: User, laptop_product: Product
    ) -> None:
        """Test transaction with very large amount."""
        transaction = Transaction(
            buyer=buyer_user,
            seller=seller_user,
            product=laptop_product,
            transaction_amount=999999999,
        )

        assert transaction.transaction_amount == 999999999

    def test_detailed_transaction_with_optional_fields(
        self, buyer_user: User, seller_user: User, simple_product: Product
    ) -> None:
        """Test detailed transaction with and without optional fields."""
        t1 = DetailedTransaction(
            buyer=buyer_user,
            seller=seller_user,
            product=simple_product,
            transaction_amount=100,
        )
        assert t1.transaction_date == ""

        t2 = DetailedTransaction(
            buyer=buyer_user,
            seller=seller_user,
            product=simple_product,
            transaction_amount=100,
            transaction_date="2025-01-20",
        )
        assert t2.transaction_date == "2025-01-20"
