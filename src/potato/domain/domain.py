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
    TypeVarTuple,
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

from .aggregates import Aggregate


class FieldProxy:
    """
    Proxy object for referencing fields from a Domain model.

    FieldProxy enables cross-model field references using the syntax:
    `Annotated[type, DomainClass.field_name]` or
    `Annotated[type, DomainClass("alias").field_name]` for multiple instances

    This is used in two contexts:
    1. ViewDTO field mappings: Map DTO fields to differently-named Domain fields
    2. Aggregate field extraction: Reference specific fields from aggregated domains

    Attributes:
        model_cls: The Domain class being referenced
        field_name: The name of the field in the Domain class
        alias: Optional alias to distinguish multiple instances of same domain

    Example:
        >>> class DomainA(Domain):
        ...     name: str
        >>>
        >>> # Single instance
        >>> class EntityDTO(ViewDTO[DomainA]):
        ...     display_name: Annotated[str, DomainA.name]  # Maps display_name -> name
        >>>
        >>> # Multiple instances
        >>> class RelationView(ViewDTO[Aggregate[DomainA, DomainA, DomainB]]):
        ...     source_name: Annotated[str, DomainA("source").name]
        ...     target_name: Annotated[str, DomainA("target").name]
    """

    def __init__(self, model_cls: type, field_name: str, alias: str | None = None):
        self.model_cls = model_cls
        self.field_name = field_name
        self.alias = alias

    def __repr__(self):
        if self.alias:
            return f"FieldProxy({self.model_cls.__name__}({self.alias!r}).{self.field_name})"
        return f"FieldProxy({self.model_cls.__name__}.{self.field_name})"


class AliasedDomainProxy:
    """
    Proxy for creating aliased field references.

    When you call Domain("alias"), it returns this proxy which creates
    FieldProxy instances with the alias attached.

    This enables syntax like: DomainA("source").name
    which returns: FieldProxy(DomainA, "name", alias="source")

    Attributes:
        domain_cls: The Domain class being aliased
        alias: The alias name for this instance

    Example:
        >>> source_proxy = DomainA("source")
        >>> source_name = source_proxy.name
        >>> print(source_name)  # FieldProxy(DomainA("source").name)
    """

    def __init__(self, domain_cls: type, alias: str):
        self.domain_cls = domain_cls
        self.alias = alias

    def __getattr__(self, field_name: str) -> FieldProxy:
        """Return a FieldProxy with the alias attached."""
        # Check if field exists in the domain class
        annotations = getattr(self.domain_cls, "__annotations__", {})
        if field_name not in annotations:
            raise AttributeError(
                f"Domain '{self.domain_cls.__name__}' has no field '{field_name}'"
            )
        return FieldProxy(self.domain_cls, field_name, alias=self.alias)

    def __repr__(self):
        return f"AliasedDomainProxy({self.domain_cls.__name__}({self.alias!r}))"


class AnnotatedTypeProxy:
    """
    Runtime proxy for Annotated type aliases to enable attribute access.

    When you have: Source = Annotated[DomainA, "source"]
    This proxy allows: Source.id to work at runtime.

    Usage:
        >>> Source = Annotated[DomainA, "source"]
        >>> source_id = get_aliased_proxy(Source).id
        >>> # source_id is FieldProxy(DomainA, "id", alias="source")
    """

    def __init__(self, annotated_type: Any):
        """Initialize from an Annotated type alias."""
        origin = get_origin(annotated_type)
        if origin is not Annotated:
            raise TypeError(f"Expected Annotated type, got {type(annotated_type)}")

        args = get_args(annotated_type)
        self.domain_cls = args[0]
        self.alias = None

        # Extract alias string from metadata
        for meta in args[1:]:
            if isinstance(meta, str):
                self.alias = meta
                break

        if self.alias is None:
            raise ValueError(
                f"No string alias found in Annotated type: {annotated_type}"
            )

    def __getattr__(self, field_name: str) -> FieldProxy:
        """Return a FieldProxy with the alias attached."""
        # Check if field exists in the domain class
        annotations = getattr(self.domain_cls, "__annotations__", {})
        if field_name not in annotations:
            raise AttributeError(
                f"Domain '{self.domain_cls.__name__}' has no field '{field_name}'"
            )
        return FieldProxy(self.domain_cls, field_name, alias=self.alias)

    def __repr__(self):
        return f"AnnotatedTypeProxy({self.domain_cls.__name__}, alias={self.alias!r})"


def get_aliased_proxy(annotated_type: Any) -> AnnotatedTypeProxy:
    """
    Get a proxy object for an Annotated type alias that enables attribute access.

    Usage:
        >>> Source = Annotated[DomainA, "source"]
        >>> SourceProxy = get_aliased_proxy(Source)
        >>> source_id = SourceProxy.id  # Returns FieldProxy(DomainA, "id", alias="source")
    """
    return AnnotatedTypeProxy(annotated_type)


class AliasedTypeMeta(type):
    """
    Metaclass for AliasedType that makes instances behave like types.

    This metaclass allows AliasedType instances to be used in generic type
    parameters while still supporting attribute access for field references.
    """

    def __call__(cls, domain_cls: type, alias: str):
        """
        Create a new type that represents the aliased domain.

        Instead of returning an instance of AliasedType, we create a new
        type dynamically that mypy will recognize as valid in generics.
        """
        # Create a new type dynamically
        # The type name includes the alias for clarity
        type_name = f"{domain_cls.__name__}_{alias}"

        # Get the metaclass of the domain class
        domain_metaclass = type(domain_cls)

        # Create a custom metaclass that provides __getattr__ for the TYPE itself
        # This allows Buyer.id to work (accessing attribute on the class, not instance)
        # It must inherit from the domain's metaclass to avoid metaclass conflicts
        class AliasedDomainMeta(domain_metaclass):  # type: ignore
            """Metaclass for the dynamically created aliased type."""

            def __getattr__(cls, field_name: str) -> FieldProxy:
                """Return a FieldProxy with the alias attached when accessing class attributes."""
                annotations = getattr(domain_cls, "__annotations__", {})
                if field_name not in annotations:
                    raise AttributeError(
                        f"Domain '{domain_cls.__name__}' has no field '{field_name}'"
                    )
                return FieldProxy(domain_cls, field_name, alias=alias)

            def __repr__(cls):
                return f"AliasedType({domain_cls.__name__}, alias={alias!r})"

        # Create the new type with the custom metaclass
        new_type = AliasedDomainMeta(
            type_name,
            (domain_cls,),  # Inherit from the domain class
            {
                "_domain_cls": domain_cls,
                "_alias": alias,
                "__module__": domain_cls.__module__,
            },
        )

        return new_type


class AliasedType(metaclass=AliasedTypeMeta):
    """
    Helper class to create type aliases that support attribute access.

    This allows you to use: Source.id where Source = AliasedType(DomainA, "source")
    And also use Source in type annotations: Aggregate[Source, Target, DomainB]

    Usage:
        >>> Source = AliasedType(DomainA, "source")
        >>> source_id = Source.id  # Returns FieldProxy(DomainA, "id", alias="source")
        >>> # Source can be used in Aggregate[Source, ...] - mypy accepts it as a type

    Note: AliasedType(domain, alias) returns a new type, not an instance.
    This is achieved through the metaclass __call__ method.
    """

    # This class body is mostly for documentation
    # The actual behavior is defined in AliasedTypeMeta.__call__

    if TYPE_CHECKING:
        # For IDE completion: tell type checkers that any attribute access returns FieldProxy
        # This is a lie for type checking, but it helps IDEs provide completion
        def __getattr__(self, name: str) -> FieldProxy: ...

    pass


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
                            DomainMeta._extract_field_mappings(cls)
                            break

        return cls

    @staticmethod
    def _extract_field_mappings(cls: type) -> None:
        """
        Extract field mappings from Annotated types with FieldProxy metadata.

        Scans the class's type hints for Annotated[type, FieldProxy] patterns
        and builds a mapping of field names to (domain_class, field_name, alias) tuples.
        This enables the build() method to automatically extract values from
        referenced domain fields, supporting both single and aliased domain instances.

        Args:
            cls: The Domain class being processed

        Side Effects:
            Sets cls.__aggregate_field_mappings__ with the extracted mappings
        """

        field_mappings: dict[str, tuple[type, str, str | None]] = {}
        try:
            type_hints = get_type_hints(cls, include_extras=True)
            for field_name, field_type in type_hints.items():
                # Skip class variables and private attributes
                if field_name.startswith("_"):
                    continue

                # Check if this is an Annotated type
                origin = get_origin(field_type)
                if origin is Annotated:
                    args = get_args(field_type)
                    # args[0] is the actual type, args[1:] are metadata
                    for metadata in args[1:]:
                        if isinstance(metadata, FieldProxy):
                            # Map field to (domain_class, domain_field_name, alias)
                            field_mappings[field_name] = (
                                metadata.model_cls,
                                metadata.field_name,
                                metadata.alias,
                            )
                            break
        except Exception:
            # If we can't get type hints, just skip
            pass

        # Store field mappings on the class for use by build method
        cls.__aggregate_field_mappings__ = field_mappings  # type: ignore

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


AggregateD = TypeVarTuple("AggregateD")

A = Aggregate[*AggregateD]


class Domain[T: A | None = None](BaseModel, metaclass=DomainMeta):
    """
    Base class for all domain models with optional aggregate support.

    Domain extends Pydantic's BaseModel with additional features:
    1. Field access as class attributes (e.g., DomainA.name)
    2. Aggregate support via Domain[Aggregate[Type1, Type2, ...]]
    3. Aliasing via DomainA.alias("first") for multiple instances
    4. Compile-time validation of field mappings and aggregate declarations

    Basic Usage:
        >>> class DomainA(Domain):
        ...     id: int
        ...     name: str
        ...     value: str

    Aggregate Usage:
        >>> class DomainC(Domain[Aggregate[DomainA, DomainB]]):
        ...     entity_a: DomainA
        ...     description: Annotated[str, DomainB.description]

    Aliasing Usage:
        >>> Source = DomainA.alias("source")
        >>> Target = DomainA.alias("target")
        >>> class RelationView(ViewDTO[Aggregate[Source, Target, DomainB]]):
        ...     source_id: Annotated[int, Source.id]
        ...     target_id: Annotated[int, Target.id]

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
