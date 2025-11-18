"""Domain class definitions for testing."""

from __future__ import annotations

from typing import Annotated

from potato.domain import Aggregate, Domain


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


class Order(Aggregate[User, Price, Product]):
    """An aggregate domain composed of multiple other domains."""

    customer: User
    seller: User
    price_amount: Annotated[int, Price.amount]
    product: Product


# Aliased types for multi-instance scenarios
Buyer = User.alias("buyer")
Seller = User.alias("seller")

