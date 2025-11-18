"""Aggregate domain fixtures."""

from __future__ import annotations

import pytest

from .domains import Order, Price, Product, User


@pytest.fixture
def simple_order(
    simple_user: User, seller_user: User, usd_price: Price, simple_product: Product
) -> Order:
    """A basic order with minimal fields."""
    return Order(
        customer=simple_user,
        seller=seller_user,
        price_amount=usd_price.amount,
        product=simple_product,
    )


@pytest.fixture
def laptop_order(
    buyer_user: User, seller_user: User, high_price: Price, laptop_product: Product
) -> Order:
    """An order for a laptop."""
    return Order(
        customer=buyer_user,
        seller=seller_user,
        price_amount=high_price.amount,
        product=laptop_product,
    )

