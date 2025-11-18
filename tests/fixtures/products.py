"""Product domain fixtures."""

from __future__ import annotations

import pytest

from .domains import Product


@pytest.fixture
def simple_product() -> Product:
    """A basic product."""
    return Product(id=1, name="Widget", description="A useful widget")


@pytest.fixture
def laptop_product() -> Product:
    """A laptop product."""
    return Product(id=100, name="Laptop", description="High-performance laptop")


@pytest.fixture
def smartphone_product() -> Product:
    """A smartphone product."""
    return Product(id=200, name="Smartphone", description="Latest model")

