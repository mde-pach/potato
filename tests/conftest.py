"""Pytest configuration and shared fixtures for all tests.

This module imports all fixtures from the fixtures package to make them
available to all tests.
"""

from __future__ import annotations

# Register fixture modules with pytest
# This ensures pytest discovers all fixtures in these modules
pytest_plugins = [
    "tests.fixtures.aggregates",
    "tests.fixtures.classes",
    "tests.fixtures.prices",
    "tests.fixtures.products",
    "tests.fixtures.users",
]

# Import domain classes for convenience
from .fixtures.domains import Buyer, Order, Price, Product, Seller, User  # noqa: E402

__all__ = [
    "Buyer",
    "Order",
    "Price",
    "Product",
    "Seller",
    "User",
]
