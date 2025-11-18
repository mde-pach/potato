"""Test fixtures package.

This package contains all pytest fixtures organized by domain and type.
"""

# Import all fixture modules to ensure pytest discovers them
from . import (
    aggregates,  # noqa: F401
    classes,  # noqa: F401
    prices,  # noqa: F401
    products,  # noqa: F401
    users,  # noqa: F401
)

# Export domain classes for convenience
from .domains import Buyer, Order, Price, Product, Seller, User

__all__ = [
    "Buyer",
    "Order",
    "Price",
    "Product",
    "Seller",
    "User",
]
