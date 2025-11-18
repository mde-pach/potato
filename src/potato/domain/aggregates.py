"""Aggregate module for Domain-Driven Design aggregates.

Aggregates are special Domain classes that encapsulate other domains,
representing a consistency boundary in your domain model.
"""

from typing import Any, TypeVarTuple, dataclass_transform

from pydantic._internal._model_construction import (
    NoInitField,
    PydanticModelField,
    PydanticModelPrivateAttr,
)

from .domain import Domain, DomainMeta


@dataclass_transform(
    kw_only_default=True,
    field_specifiers=(PydanticModelField, NoInitField, PydanticModelPrivateAttr),
)
class AggregateMeta(DomainMeta):  # type: ignore
    """Metaclass for Aggregate that handles variadic generic parameters."""

    def __getitem__(cls, params: Any) -> type:
        """Handle Aggregate[Type1, Type2, ...] subscripting."""
        # Normalize params to always be a tuple
        if not isinstance(params, tuple):
            params = (params,)

        # Create a new class that inherits from Aggregate
        # and stores the aggregate types as class variable
        class_dict = {
            "__aggregate_domain_types__": params,
            "__module__": cls.__module__,
        }

        # Create new class name
        type_names = "_".join(
            t.__name__ if hasattr(t, "__name__") else str(t) for t in params
        )
        new_class_name = f"{cls.__name__}[{type_names}]"

        # Create the new class
        new_class = type(cls)(new_class_name, (cls,), class_dict)

        # Extract field mappings for this aggregate
        if hasattr(Domain, "__class__") and hasattr(
            Domain.__class__, "_extract_field_mappings"
        ):
            Domain.__class__._extract_field_mappings(new_class)  # type: ignore

        return new_class


D = TypeVarTuple("D")


class Aggregate[*D](Domain, metaclass=AggregateMeta):  # type: ignore
    """
    Base class for aggregate domains that encapsulate multiple other domains.

    In Domain-Driven Design, an Aggregate is a cluster of domain objects that
    are treated as a single unit. The Aggregate ensures consistency of changes
    being made within the boundary.

    Usage:
        >>> class Order(Aggregate[User, Product, Price]):
        ...     customer: User
        ...     product: Product
        ...     price_amount: Annotated[int, Price.amount]

    The generic parameters specify which domains this aggregate encapsulates.
    """

    pass
