"""
Domain module - Core domain model implementation with aggregate support.

This module provides the Domain base class and supporting infrastructure for
building rich domain models with compile-time validation of aggregate relationships.
"""

from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    ClassVar,
    Self,
    dataclass_transform,
    get_args,
    get_origin,
    get_type_hints,
)

from pydantic import BaseModel
from pydantic._internal._model_construction import (
    ModelMetaclass,
    NoInitField,
    PydanticModelField,
    PydanticModelPrivateAttr,
)

from potato.types import (
    AliasedType,
    FieldProxy,
)
from potato.introspection import extract_field_mappings

if TYPE_CHECKING:
    from .aggregates import Aggregate


@dataclass_transform(
    kw_only_default=True,
    field_specifiers=(PydanticModelField, NoInitField, PydanticModelPrivateAttr),
)
class DomainMeta(ModelMetaclass):
    """
    Metaclass for Domain models with aggregate support.

    This metaclass extends Pydantic's ModelMetaclass to provide:
    1. Field access as class attributes (e.g., User.username returns FieldProxy)
    2. Aggregate relationship extraction and validation
    3. Field mapping extraction for aggregate build() methods

    When a Domain is defined with Aggregate[Type1, Type2, ...], this metaclass:
    - Stores the aggregate types in __aggregate_domain_types__
    - Extracts field mappings from Annotated type hints
    - Enables the automatic build() method for aggregates
    """

    def __new__(
        mcs: type,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        **kwargs: Any,
    ) -> type:
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)  # type: ignore

        # Check if any base class has Pydantic generic metadata with Aggregate
        for base in cls.__bases__:
            if hasattr(base, "__pydantic_generic_metadata__"):
                metadata = base.__pydantic_generic_metadata__
                # metadata['args'] contains the type arguments passed to the generic
                if "args" in metadata and metadata["args"]:
                    # Check if the first argument is Aggregate[...]
                    first_arg = metadata["args"][0]
                    aggregate_origin = get_origin(first_arg)
                    if aggregate_origin is not None:
                        # Get the domain types from Aggregate[User, Price, ...]
                        aggregate_args = get_args(first_arg)
                        if aggregate_args:
                            # Store metadata for the static build method
                            cls.__aggregate_domain_types__ = aggregate_args  # type: ignore
                            # Extract field mappings
                            cls.__aggregate_field_mappings__ = extract_field_mappings(cls)  # type: ignore
                            break

        return cls

    if not TYPE_CHECKING:

        def __getattr__(cls, name: str):
            """
            Enable field access as class attributes (e.g., DomainA.name).

            When accessing a field on a Domain class (not instance), return a
            FieldProxy that can be used in Annotated type hints for field mappings.

            Args:
                name: The attribute name being accessed

            Returns:
                FieldProxy for annotated fields, or delegates to parent for others

            Example:
                >>> DomainA.name  # Returns FieldProxy(DomainA, "name")
            """
            if cls.__name__ == "Domain":
                return super().__getattr__(name)

            annotations = getattr(cls, "__annotations__", {})

            if name in annotations:
                # Don't return FieldProxy when Pydantic is collecting model fields
                # to determine default values. This prevents FieldProxy from being
                # used as a default value for required fields.
                import inspect

                frame = inspect.currentframe()
                try:
                    caller_frame = frame.f_back
                    if (
                        caller_frame
                        and "collect_model_fields" in caller_frame.f_code.co_name
                    ):
                        # Pydantic is collecting fields, don't provide FieldProxy as default
                        raise AttributeError(
                            f"type object '{cls.__name__}' has no attribute '{name}'"
                        )
                finally:
                    del frame

                return FieldProxy(cls, name)

            return super().__getattr__(name)


class Domain(BaseModel, metaclass=DomainMeta):
    """
    Base class for all domain models.

    Domain extends Pydantic's BaseModel with additional features:
    1. Field access as class attributes (e.g., DomainA.name)
    2. Aliasing via DomainA.alias("first") for multiple instances
    3. Compile-time validation of field mappings and aggregate declarations

    Basic Usage:
        >>> class DomainA(Domain):
        ...     id: int
        ...     name: str
        ...     value: str

    For aggregates that encapsulate multiple domains, use the Aggregate class:
        >>> class Order(Aggregate[User, Product, Price]):
        ...     customer: User
        ...     product_name: Annotated[str, Product.name]
        ...     price_amount: Annotated[int, Price.amount]

    Aliasing Usage (for multiple instances of the same domain):
        >>> Buyer = User.alias("buyer")
        >>> Seller = User.alias("seller")
        >>> class Transaction(Aggregate[Buyer, Seller, Product]):
        ...     buyer_id: Annotated[int, Buyer.id]
        ...     seller_id: Annotated[int, Seller.id]
        ...     product: Product

    Attributes:
        __aggregate_domain_types__: Tuple of Domain types in the aggregate
        __aggregate_field_mappings__: Mapping of fields to (domain_class, field_name, alias)
    """

    __aggregate_domain_types__: ClassVar[tuple[type, ...]] = ()
    __aggregate_field_mappings__: ClassVar[dict[str, tuple[type, str, str | None]]] = {}

    @classmethod
    def alias(cls: type[Self], alias_name: str) -> type[Self]:
        """
        Create an aliased type reference for this domain.

        This enables using multiple instances of the same domain type in aggregates.

        Args:
            alias_name: The alias to use for this instance

        Returns:
            A type that behaves like the original Domain class but with alias metadata.
            Supports field access (e.g., Source.id) and can be used in Aggregate declarations.

        Example:
            >>> Source = DomainA.alias("source")
            >>> Target = DomainA.alias("target")
            >>> class RelationView(ViewDTO[Aggregate[Source, Target, DomainB]]):
            ...     source_id: Annotated[int, Source.id]
            ...     target_id: Annotated[int, Target.id]
        """
        return AliasedType(cls, alias_name)  # type: ignore[return-value, call-arg]
