from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    get_args,
    get_origin,
)

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
        >>> # Multiple instances with aliasing
        >>> Source = DomainA.alias("source")
        >>> Target = DomainA.alias("target")
        >>> class RelationView(ViewDTO[Aggregate[Source, Target, DomainB]]):
        ...     source_name: Annotated[str, Source.name]
        ...     target_name: Annotated[str, Target.name]
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

        # Explicitly set attributes after creation to ensure they're accessible
        # This is needed because Pydantic's metaclass may interfere with namespace attributes
        setattr(new_type, "_domain_cls", domain_cls)
        setattr(new_type, "_alias", alias)

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
