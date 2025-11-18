"""Price domain fixtures."""

from __future__ import annotations

import pytest

from .domains import Price


@pytest.fixture
def usd_price() -> Price:
    """A price in USD."""
    return Price(amount=100, currency="USD")


@pytest.fixture
def eur_price() -> Price:
    """A price in EUR."""
    return Price(amount=85, currency="EUR")


@pytest.fixture
def high_price() -> Price:
    """A high-value price."""
    return Price(amount=1500, currency="USD")

