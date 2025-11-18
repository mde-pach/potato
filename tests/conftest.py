"""Pytest configuration and shared fixtures for all tests."""

from __future__ import annotations

from typing import Annotated

import pytest

from potato.domain import Domain
from potato.domain.aggregates import Aggregate

# =============================================================================
# Domain Fixtures
# =============================================================================


class User(Domain):
    """A simple domain model with required and optional fields."""

    id: int
    username: str
    email: str
    tutor: str | None = None
    friends: list[str] = []


class Price(Domain):
    """Domain representing a price with amount and currency."""

    amount: int
    currency: str


class Product(Domain):
    """Domain representing a product."""

    id: int
    name: str
    description: str


class Order(Domain[Aggregate[User, Price, Product]]):
    """An aggregate domain composed of multiple other domains."""

    customer: User
    seller: User
    price_amount: Annotated[int, Price.amount]
    product: Product


# Aliased types for multi-instance scenarios
Buyer = User.alias("buyer")
Seller = User.alias("seller")


# =============================================================================
# User Fixtures
# =============================================================================


@pytest.fixture
def simple_user():
    """A user with only required fields."""
    return User(id=1, username="alice", email="alice@example.com")


@pytest.fixture
def user_with_tutor():
    """A user with a tutor."""
    return User(id=2, username="bob", email="bob@example.com", tutor="alice")


@pytest.fixture
def user_with_friends():
    """A user with friends."""
    return User(
        id=3,
        username="charlie",
        email="charlie@example.com",
        friends=["alice", "bob"],
    )


@pytest.fixture
def complete_user():
    """A user with all fields populated."""
    return User(
        id=4,
        username="diana",
        email="diana@example.com",
        tutor="alice",
        friends=["bob", "charlie"],
    )


@pytest.fixture
def buyer_user():
    """A user representing a buyer in transactions."""
    return User(id=10, username="buyer1", email="buyer1@example.com")


@pytest.fixture
def seller_user():
    """A user representing a seller in transactions."""
    return User(id=20, username="seller1", email="seller1@example.com")


# =============================================================================
# Product Fixtures
# =============================================================================


@pytest.fixture
def simple_product():
    """A basic product."""
    return Product(id=1, name="Widget", description="A useful widget")


@pytest.fixture
def laptop_product():
    """A laptop product."""
    return Product(id=100, name="Laptop", description="High-performance laptop")


@pytest.fixture
def smartphone_product():
    """A smartphone product."""
    return Product(id=200, name="Smartphone", description="Latest model")


# =============================================================================
# Price Fixtures
# =============================================================================


@pytest.fixture
def usd_price():
    """A price in USD."""
    return Price(amount=100, currency="USD")


@pytest.fixture
def eur_price():
    """A price in EUR."""
    return Price(amount=85, currency="EUR")


@pytest.fixture
def high_price():
    """A high-value price."""
    return Price(amount=1500, currency="USD")


# =============================================================================
# Aggregate Fixtures
# =============================================================================


@pytest.fixture
def simple_order(simple_user, seller_user, usd_price, simple_product):
    """A basic order with minimal fields."""
    return Order(
        customer=simple_user,
        seller=seller_user,
        price_amount=usd_price.amount,
        product=simple_product,
    )


@pytest.fixture
def laptop_order(buyer_user, seller_user, high_price, laptop_product):
    """An order for a laptop."""
    return Order(
        customer=buyer_user,
        seller=seller_user,
        price_amount=high_price.amount,
        product=laptop_product,
    )


# =============================================================================
# Expose domain classes for tests
# =============================================================================


@pytest.fixture
def user_class():
    """Return the User domain class."""
    return User


@pytest.fixture
def product_class():
    """Return the Product domain class."""
    return Product


@pytest.fixture
def price_class():
    """Return the Price domain class."""
    return Price


@pytest.fixture
def order_class():
    """Return the Order domain class."""
    return Order


@pytest.fixture
def buyer_alias():
    """Return the Buyer alias."""
    return Buyer


@pytest.fixture
def seller_alias():
    """Return the Seller alias."""
    return Seller
