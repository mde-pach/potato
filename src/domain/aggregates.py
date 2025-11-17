"""
Aggregates module - Support for composite domain models.

This module provides the Aggregate marker type used to declare domains that
compose multiple other domain types.
"""

from typing import TypeVarTuple

D = TypeVarTuple("D")


class Aggregate[*D]:
    """
    Marker class for declaring aggregate domain relationships.

    Aggregate is used in generic type parameters to indicate that a Domain
    is composed of multiple other Domain types. The mypy plugin validates
    that all referenced Domain types are properly declared.

    Type Parameters:
        *D: Variable-length tuple of Domain types that compose this aggregate

    Usage:
        >>> class Order(Domain[Aggregate[User, Price, Product]]):
        ...     user: User
        ...     price: Annotated[int, Price.amount]
        ...     product: Product

    The Aggregate declaration:
    1. Documents the domain dependencies explicitly
    2. Enables compile-time validation via mypy plugin
    3. Provides metadata for automatic build() method generation

    Note:
        This is a marker class and should not be instantiated directly.
        It's only used as a generic type parameter for Domain classes.
    """

    pass
