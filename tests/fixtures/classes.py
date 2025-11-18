"""Domain class fixtures."""

from __future__ import annotations

from typing import Type

import pytest

from .domains import Buyer, Order, Price, Product, Seller, User


@pytest.fixture
def user_class() -> Type[User]:
    """Return the User domain class."""
    return User


@pytest.fixture
def product_class() -> Type[Product]:
    """Return the Product domain class."""
    return Product


@pytest.fixture
def price_class() -> Type[Price]:
    """Return the Price domain class."""
    return Price


@pytest.fixture
def order_class() -> Type[Order]:
    """Return the Order domain class."""
    return Order


@pytest.fixture
def buyer_alias() -> Type[Buyer]:
    """Return the Buyer alias."""
    return Buyer


@pytest.fixture
def seller_alias() -> Type[Seller]:
    """Return the Seller alias."""
    return Seller

