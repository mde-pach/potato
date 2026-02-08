"""Aggregate module for Domain-Driven Design aggregates.

Aggregates are Domain classes that compose other domains.
Domain types are inferred from field annotations — no generic syntax needed.

Usage:
    class OrderAggregate(Aggregate):
        customer: User
        product: Product
        amount: int  # aggregate's own field

    # Field access for ViewDTO mapping:
    OrderAggregate.customer.username  # → FieldProxy(User, "username", namespace="customer")
"""

from typing import Any, dataclass_transform, get_type_hints

from pydantic._internal._model_construction import (
    NoInitField,
    PydanticModelField,
    PydanticModelPrivateAttr,
)

from potato.types import DomainFieldAccessor

from .domain import Domain, DomainMeta


@dataclass_transform(
    kw_only_default=True,
    field_specifiers=(PydanticModelField, NoInitField, PydanticModelPrivateAttr),
)
class AggregateMeta(DomainMeta):  # type: ignore
    """Metaclass for Aggregate that infers domain types from field annotations."""

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        **kwargs: Any,
    ) -> type:
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        # Skip validation for the base Aggregate class
        if name == "Aggregate":
            return cls

        # Infer domain types from field annotations
        domain_fields: dict[str, type] = {}  # field_name → Domain subclass
        try:
            hints = get_type_hints(cls)
        except Exception:
            hints = {}

        for field_name, field_type in hints.items():
            if field_name.startswith("_"):
                continue
            if isinstance(field_type, type) and issubclass(field_type, Domain) and field_type is not Domain:
                domain_fields[field_name] = field_type

        cls.__aggregate_domain_fields__ = domain_fields  # type: ignore

        return cls

    def __getattr__(cls, name: str):
        """
        Return DomainFieldAccessor for Domain-typed fields.

        Aggregate.field → DomainFieldAccessor if field is a Domain type
        Otherwise, fall back to normal FieldProxy behavior.
        """
        # Don't intercept during Pydantic model field collection
        import inspect
        frame = inspect.currentframe()
        try:
            # Check up to 5 frames for collect_model_fields
            check_frame = frame.f_back
            for _ in range(5):
                if check_frame is None:
                    break
                if "collect_model_fields" in check_frame.f_code.co_name:
                    raise AttributeError(
                        f"type object '{cls.__name__}' has no attribute '{name}'"
                    )
                check_frame = check_frame.f_back
        finally:
            del frame

        # Avoid infinite recursion: look up __aggregate_domain_fields__ through MRO dicts
        domain_fields: dict[str, type] = {}
        for klass in cls.__mro__:
            if "__aggregate_domain_fields__" in klass.__dict__:
                domain_fields = klass.__dict__["__aggregate_domain_fields__"]
                break

        if name in domain_fields:
            return DomainFieldAccessor(domain_fields[name], namespace=name)

        # Fall back to DomainMeta behavior for aggregate's own non-domain fields
        return super().__getattr__(name)


class Aggregate(Domain, metaclass=AggregateMeta):
    """
    Base class for aggregate domains that compose multiple other domains.

    Domain types are inferred from field annotations — just declare fields
    with Domain types and the framework handles the rest.

    Usage:
        >>> class Order(Aggregate):
        ...     customer: User
        ...     product: Product
        ...     amount: int

        >>> Order.customer.username  # → FieldProxy(User, "username", namespace="customer")
    """
    pass
