"""Tests for Aggregate domain functionality."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from potato.domain.aggregates import Aggregate

from ..fixtures.domains import Price, Product, User


# =============================================================================
# Aggregate Test Classes (new field-based syntax, no generics)
# =============================================================================


class SimpleOrder(Aggregate):
    """Simple aggregate with two domains."""

    customer: User
    product: Product


class OrderWithFields(Aggregate):
    """Aggregate with domain fields and scalar fields."""

    customer: User
    price_amount: int
    price_currency: str
    product: Product


class ComplexOrder(Aggregate):
    """Complex aggregate with multiple users and extra fields."""

    customer: User
    seller: User
    price_amount: int
    product: Product
    order_notes: str = ""


# =============================================================================
# Test Aggregate Creation
# =============================================================================


class TestAggregateCreation:
    """Test creating aggregate domains."""

    def test_create_simple_aggregate(
        self, simple_user: User, simple_product: Product
    ) -> None:
        """Test creating a simple aggregate."""
        order = SimpleOrder(customer=simple_user, product=simple_product)

        assert order.customer.id == 1
        assert order.customer.username == "alice"
        assert order.product.id == 1
        assert order.product.name == "Widget"

    def test_create_aggregate_with_fields(
        self, simple_user: User, usd_price: Price, simple_product: Product
    ) -> None:
        """Test creating aggregate with scalar fields."""
        order = OrderWithFields(
            customer=simple_user,
            price_amount=usd_price.amount,
            price_currency=usd_price.currency,
            product=simple_product,
        )

        assert order.customer.username == "alice"
        assert order.price_amount == 100
        assert order.price_currency == "USD"
        assert order.product.name == "Widget"

    def test_create_complex_aggregate(
        self,
        simple_user: User,
        seller_user: User,
        usd_price: Price,
        simple_product: Product,
    ) -> None:
        """Test creating complex aggregate with multiple users."""
        order = ComplexOrder(
            customer=simple_user,
            seller=seller_user,
            price_amount=usd_price.amount,
            product=simple_product,
            order_notes="Rush delivery",
        )

        assert order.customer.username == "alice"
        assert order.seller.username == "seller1"
        assert order.price_amount == 100
        assert order.product.name == "Widget"
        assert order.order_notes == "Rush delivery"

    def test_create_order_from_fixture(self, simple_order) -> None:
        """Test using order fixture."""
        assert simple_order.customer.username == "alice"
        assert simple_order.seller.username == "seller1"
        assert simple_order.price_amount == 100
        assert simple_order.product.name == "Widget"


class TestAggregateAccess:
    """Test accessing aggregate fields."""

    def test_access_nested_domain_fields(self, simple_order) -> None:
        """Test accessing fields from nested domains."""
        assert simple_order.customer.id == 1
        assert simple_order.customer.email == "alice@example.com"
        assert simple_order.seller.id == 20
        assert simple_order.product.description == "A useful widget"

    def test_access_scalar_fields(self, simple_order) -> None:
        """Test accessing scalar fields."""
        assert simple_order.price_amount == 100
        assert isinstance(simple_order.price_amount, int)

    def test_modify_nested_domain(self, simple_order) -> None:
        """Test modifying nested domain fields."""
        original_username = simple_order.customer.username
        simple_order.customer.username = "new_username"

        assert simple_order.customer.username == "new_username"
        assert simple_order.customer.username != original_username

    def test_replace_nested_domain(self, simple_order, complete_user: User) -> None:
        """Test replacing entire nested domain."""
        simple_order.customer = complete_user

        assert simple_order.customer.id == 4
        assert simple_order.customer.username == "diana"


class TestAggregateSerialization:
    """Test aggregate serialization."""

    def test_model_dump_includes_nested_domains(self, simple_order) -> None:
        """Test that model_dump includes all nested domains."""
        data = simple_order.model_dump()

        assert "customer" in data
        assert "seller" in data
        assert "product" in data
        assert "price_amount" in data

        assert data["customer"]["username"] == "alice"
        assert data["seller"]["username"] == "seller1"
        assert data["product"]["name"] == "Widget"
        assert data["price_amount"] == 100

    def test_model_dump_json(self, simple_order) -> None:
        """Test JSON serialization of aggregate."""
        json_str = simple_order.model_dump_json()

        assert isinstance(json_str, str)
        assert "alice" in json_str
        assert "seller1" in json_str
        assert "Widget" in json_str

    def test_model_dump_exclude(self, simple_order) -> None:
        """Test model_dump with exclude option."""
        data = simple_order.model_dump(exclude={"seller"})

        assert "customer" in data
        assert "seller" not in data
        assert "product" in data


class TestAggregateValidation:
    """Test aggregate validation."""

    def test_missing_required_domain_raises_error(self, simple_user: User) -> None:
        """Test that missing required domain raises error."""
        with pytest.raises((ValidationError, TypeError)):
            SimpleOrder(customer=simple_user)  # type: ignore[call-arg]

    def test_missing_scalar_field_raises_error(
        self, simple_user: User, simple_product: Product
    ) -> None:
        """Test that missing scalar field raises error."""
        with pytest.raises(ValidationError):
            OrderWithFields(
                customer=simple_user,
                price_amount=100,
                # Missing price_currency
                product=simple_product,
            )

    def test_wrong_type_for_scalar_field(
        self, simple_user: User, simple_product: Product
    ) -> None:
        """Test that wrong type for scalar field raises error."""
        with pytest.raises(ValidationError):
            OrderWithFields(
                customer=simple_user,
                price_amount="not_an_int",  # Should be int
                price_currency="USD",
                product=simple_product,
            )

    def test_wrong_domain_type_raises_error(
        self, simple_user: User, usd_price: Price
    ) -> None:
        """Test that wrong domain type raises error."""
        with pytest.raises(ValidationError):
            SimpleOrder(customer=simple_user, product=usd_price)


class TestAggregateEquality:
    """Test aggregate equality."""

    def test_same_data_equal(self, simple_user: User, simple_product: Product) -> None:
        """Test that aggregates with same data are equal."""
        order1 = SimpleOrder(customer=simple_user, product=simple_product)
        order2 = SimpleOrder(customer=simple_user, product=simple_product)

        assert order1 == order2

    def test_different_nested_domain_not_equal(
        self, simple_user: User, complete_user: User, simple_product: Product
    ) -> None:
        """Test that different nested domains make aggregates unequal."""
        order1 = SimpleOrder(customer=simple_user, product=simple_product)
        order2 = SimpleOrder(customer=complete_user, product=simple_product)

        assert order1 != order2

    def test_different_scalar_field_not_equal(
        self,
        simple_user: User,
        simple_product: Product,
        usd_price: Price,
        eur_price: Price,
    ) -> None:
        """Test that different scalar fields make aggregates unequal."""
        order1 = OrderWithFields(
            customer=simple_user,
            price_amount=usd_price.amount,
            price_currency=usd_price.currency,
            product=simple_product,
        )
        order2 = OrderWithFields(
            customer=simple_user,
            price_amount=eur_price.amount,
            price_currency=eur_price.currency,
            product=simple_product,
        )

        assert order1 != order2


class TestAggregateComplexScenarios:
    """Test complex aggregate scenarios."""

    def test_multiple_instances_same_domain_type(
        self,
        simple_user: User,
        seller_user: User,
        usd_price: Price,
        simple_product: Product,
    ) -> None:
        """Test aggregate with multiple instances of same domain type."""
        order = ComplexOrder(
            customer=simple_user,
            seller=seller_user,
            price_amount=usd_price.amount,
            product=simple_product,
        )

        assert order.customer.id != order.seller.id
        assert order.customer.username != order.seller.username

    def test_aggregate_with_optional_fields(
        self,
        simple_user: User,
        seller_user: User,
        usd_price: Price,
        simple_product: Product,
    ) -> None:
        """Test aggregate with optional fields."""
        order = ComplexOrder(
            customer=simple_user,
            seller=seller_user,
            price_amount=usd_price.amount,
            product=simple_product,
        )

        assert order.order_notes == ""

    def test_aggregate_with_all_fields(
        self,
        complete_user: User,
        seller_user: User,
        high_price: Price,
        laptop_product: Product,
    ) -> None:
        """Test aggregate with all fields populated."""
        order = ComplexOrder(
            customer=complete_user,
            seller=seller_user,
            price_amount=high_price.amount,
            product=laptop_product,
            order_notes="VIP customer - priority shipping",
        )

        assert order.customer.tutor == "alice"
        assert order.customer.friends == ["bob", "charlie"]
        assert order.price_amount == 1500
        assert order.product.name == "Laptop"
        assert order.order_notes == "VIP customer - priority shipping"


class TestAggregateFieldExtraction:
    """Test field extraction patterns."""

    def test_scalar_fields(
        self, simple_user: User, usd_price: Price, simple_product: Product
    ) -> None:
        """Test scalar fields in aggregate."""
        order = OrderWithFields(
            customer=simple_user,
            price_amount=usd_price.amount,
            price_currency=usd_price.currency,
            product=simple_product,
        )

        assert order.price_amount == usd_price.amount
        assert order.price_currency == usd_price.currency

    def test_mix_domains_and_scalars(
        self, simple_user: User, usd_price: Price, simple_product: Product
    ) -> None:
        """Test mixing full domains and scalar fields."""
        order = OrderWithFields(
            customer=simple_user,
            price_amount=usd_price.amount,
            price_currency=usd_price.currency,
            product=simple_product,
        )

        assert order.customer.username == "alice"
        assert order.customer.email == "alice@example.com"
        assert order.price_amount == 100
        assert order.price_currency == "USD"
        assert order.product.name == "Widget"
        assert order.product.description == "A useful widget"


class TestAggregateFieldAccess:
    """Test DomainFieldAccessor for Aggregate field access."""

    def test_aggregate_field_returns_accessor(self) -> None:
        """Test that accessing a domain field on Aggregate returns DomainFieldAccessor."""
        from potato.types import DomainFieldAccessor
        accessor = SimpleOrder.customer
        assert isinstance(accessor, DomainFieldAccessor)

    def test_aggregate_field_accessor_returns_field_proxy(self) -> None:
        """Test that DomainFieldAccessor returns FieldProxy on attribute access."""
        from potato.types import FieldProxy
        proxy = SimpleOrder.customer.username
        assert isinstance(proxy, FieldProxy)
        assert proxy.model_cls is User
        assert proxy.field_name == "username"
        assert proxy.namespace == "customer"

    def test_aggregate_field_accessor_invalid_field(self) -> None:
        """Test that accessing non-existent field raises AttributeError."""
        with pytest.raises(AttributeError):
            SimpleOrder.customer.nonexistent

    def test_aggregate_non_domain_field_returns_field_proxy(self) -> None:
        """Test that non-domain fields still return FieldProxy."""
        from potato.types import FieldProxy
        proxy = OrderWithFields.price_amount
        assert isinstance(proxy, FieldProxy)
        assert proxy.field_name == "price_amount"
