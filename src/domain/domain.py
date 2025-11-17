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

from .aggregates import Aggregate
from .aggregates import D as AggregateD


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
        >>> class User(Domain):
        ...     username: str
        >>>
        >>> # Single instance
        >>> class UserDTO(ViewDTO[User]):
        ...     login: Annotated[str, User.username]  # Maps login -> username
        >>>
        >>> # Multiple instances
        >>> class OrderView(ViewDTO[Aggregate[User, User, Product]]):
        ...     buyer_name: Annotated[str, User("buyer").username]
        ...     seller_name: Annotated[str, User("seller").username]
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

    This enables syntax like: User("buyer").username
    which returns: FieldProxy(User, "username", alias="buyer")

    Attributes:
        domain_cls: The Domain class being aliased
        alias: The alias name for this instance

    Example:
        >>> buyer_proxy = User("buyer")
        >>> buyer_username = buyer_proxy.username
        >>> print(buyer_username)  # FieldProxy(User("buyer").username)
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

    @classmethod
    def alias(cls, alias_name: str) -> AliasedDomainProxy:
        """
        Create an aliased reference to this Domain class.

        Use this to distinguish between multiple instances of the same domain type
        in aggregates or ViewDTOs.
        """
        return AliasedDomainProxy(cls, alias_name)

    if not TYPE_CHECKING:

        def __call__(cls, *args: Any, **kwargs: Any) -> AliasedDomainProxy | Self:
            """
            Handle Domain instantiation and aliasing.

            - Domain() or Domain(field=value) -> Create instance
            - Domain("alias") -> Return AliasedDomainProxy for field references

            Args:
                *args: Positional arguments for instantiation or alias
                **kwargs: Keyword arguments for instantiation

            Returns:
                AliasedDomainProxy if called with single string, else Domain instance

            Example:
                >>> user = User(id=1, username="alice")  # Instance
                >>> buyer_proxy = User("buyer")  # AliasedDomainProxy
                >>> buyer_id = User("buyer").id  # FieldProxy with alias
            """
            # If called with a single string argument, return aliased proxy
            if len(args) == 1 and isinstance(args[0], str) and not kwargs:
                return cls.alias(args[0])

            # Otherwise, normal instantiation
            return super(DomainMeta, cls).__call__(*args, **kwargs)

        def __getattr__(cls, name: str):
            """
            Enable field access as class attributes (e.g., User.username).

            When accessing a field on a Domain class (not instance), return a
            FieldProxy that can be used in Annotated type hints for field mappings.

            Args:
                name: The attribute name being accessed

            Returns:
                FieldProxy for annotated fields, or delegates to parent for others

            Example:
                >>> User.username  # Returns FieldProxy(User, "username")
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


A = Aggregate[*AggregateD]


class Domain[T: A | None = None](BaseModel, metaclass=DomainMeta):
    """
    Base class for all domain models with optional aggregate support.

    Domain extends Pydantic's BaseModel with additional features:
    1. Field access as class attributes (e.g., User.username)
    2. Aggregate support via Domain[Aggregate[Type1, Type2, ...]]
    3. Compile-time validation of field mappings and aggregate declarations

    Basic Usage:
        >>> class User(Domain):
        ...     id: int
        ...     username: str
        ...     email: str

    Aggregate Usage:
        >>> class Order(Domain[Aggregate[User, Price]]):
        ...     user: User
        ...     price: Annotated[int, Price.amount]

    Attributes:
        __aggregate_domain_types__: Tuple of Domain types in the aggregate
        __aggregate_field_mappings__: Mapping of fields to (domain_class, field_name, alias)
    """

    __aggregate_domain_types__: ClassVar[tuple[type, ...]] = ()
    __aggregate_field_mappings__: ClassVar[dict[str, tuple[type, str, str | None]]] = {}
