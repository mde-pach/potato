"""
DTO module - Data Transfer Objects for unidirectional data flow.

This module provides ViewDTO and BuildDTO base classes that enable type-safe
data transformations between Domain models and external representations.

The DTOs enforce a unidirectional data flow:
- BuildDTO: External data → Domain (inbound)
- ViewDTO: Domain → External data (outbound)
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

from pydantic import BaseModel, ConfigDict
from pydantic._internal._model_construction import (
    ModelMetaclass,
    NoInitField,
    PydanticModelField,
    PydanticModelPrivateAttr,
)

if TYPE_CHECKING:
    from domain import FieldProxy
else:
    from domain import FieldProxy


@dataclass_transform(
    kw_only_default=True,
    field_specifiers=(PydanticModelField, NoInitField, PydanticModelPrivateAttr),
)
class DTOMeta(ModelMetaclass):
    """
    Base metaclass for DTO classes.

    Extends Pydantic's ModelMetaclass to support generic Domain type parameters.
    """

    def __new__(
        mcs: type,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        **kwargs: Any,
    ) -> type:
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)  # type: ignore
        return cls


class ViewDTOMeta(DTOMeta):
    """
    Metaclass for ViewDTO that extracts field mappings with alias support.

    Scans ViewDTO classes for Annotated[type, FieldProxy] patterns and builds
    a mapping of DTO field names to (domain_class, field_name, alias) tuples.
    This enables the build() method to correctly map fields from multiple domains,
    including multiple instances of the same domain type.
    """

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        **kwargs: Any,
    ) -> type:
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        # Extract aggregate domain types if present
        for base in cls.__bases__:
            if hasattr(base, "__pydantic_generic_metadata__"):
                metadata = base.__pydantic_generic_metadata__
                if "args" in metadata and metadata["args"]:
                    first_arg = metadata["args"][0]
                    aggregate_origin = get_origin(first_arg)
                    if aggregate_origin is not None:
                        # Get the domain types from Aggregate[User, Profile, ...]
                        aggregate_args = get_args(first_arg)
                        if aggregate_args:
                            cls.__aggregate_domain_types__ = aggregate_args  # type: ignore
                            break

        # Extract field mappings: view_field -> (domain_class, domain_field, alias)
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

        if field_mappings:
            cls.__field_mappings__ = field_mappings  # type: ignore

        return cls


class ViewDTO[D](BaseModel, metaclass=ViewDTOMeta):
    """
    Base class for Domain-derived DTOs (outbound data flow).

    ViewDTO creates immutable data transfer objects from Domain models for
    external consumption (e.g., API responses). It supports:
    1. Single domain: ViewDTO[User]
    2. Multiple domains: ViewDTO[Aggregate[User, Profile, Settings]]
    3. Multiple instances of same domain via aliasing: User("buyer"), User("seller")
    4. Automatic field mapping via Annotated[type, Domain.field]
    5. Compile-time validation that all required Domain fields are present

    Type Parameters:
        D: The Domain class or Aggregate[Domain1, Domain2, ...] this DTO is derived from

    Usage - Single domain:
        >>> class User(Domain):
        ...     id: int
        ...     username: str
        >>>
        >>> class UserView(ViewDTO[User]):
        ...     id: int
        ...     username: str
        >>>
        >>> user = User(id=1, username="alice")
        >>> view = UserView.build(user)

    Usage - Multiple domains:
        >>> class Profile(Domain):
        ...     bio: str
        >>>
        >>> class UserProfileView(ViewDTO[Aggregate[User, Profile]]):
        ...     id: Annotated[int, User.id]
        ...     username: Annotated[str, User.username]
        ...     bio: Annotated[str, Profile.bio]
        >>>
        >>> view = UserProfileView.build(user, profile)

    Usage - Multiple instances of same domain (aliasing):
        >>> class OrderView(ViewDTO[Aggregate[User, User, Product]]):
        ...     buyer_id: Annotated[int, User("buyer").id]
        ...     buyer_name: Annotated[str, User("buyer").username]
        ...     seller_id: Annotated[int, User("seller").id]
        ...     seller_name: Annotated[str, User("seller").username]
        ...     product: Annotated[str, Product.name]
        >>>
        >>> view = OrderView.build(buyer=buyer, seller=seller, product=product)

    Attributes:
        __field_mappings__: Dict mapping DTO fields to (domain_class, field_name, alias)
        __aggregate_domain_types__: Tuple of Domain types when using Aggregate
    """

    __field_mappings__: ClassVar[dict[str, tuple[type, str, str | None]]] = {}
    __aggregate_domain_types__: ClassVar[tuple[type, ...]] = ()

    model_config = ConfigDict(
        extra="allow",
        coerce_numbers_to_str=True,
        populate_by_name=True,
        validate_by_alias=True,
        validate_by_name=True,
        frozen=True,
        from_attributes=True,
    )

    @classmethod
    def build(cls: type[Self], *entities: Any, **named_entities: Any) -> Self:
        """
        Build a ViewDTO from one or more Domain instances.

        For single domain ViewDTO[User]:
            >>> view = UserView.build(user)

        For aggregate ViewDTO[Aggregate[User, Profile]]:
            >>> view = UserProfileView.build(user, profile)

        For aggregate with duplicate domains (use named arguments):
            >>> view = OrderView.build(buyer=buyer_user, seller=seller_user, product=product)

        Automatically maps Domain fields to DTO fields, using field mappings
        defined via Annotated[type, Domain.field] or Annotated[type, Domain("alias").field].

        Args:
            *entities: Positional Domain instances (for unique domains)
            **named_entities: Named Domain instances (for aliased references)

        Returns:
            A new immutable ViewDTO instance

        Raises:
            ValueError: If wrong number or types of entities provided
        """
        # Check if this is an aggregate ViewDTO
        if (
            hasattr(cls, "__aggregate_domain_types__")
            and cls.__aggregate_domain_types__
        ):
            # Multiple domains - build entity map: (domain_class, alias) -> domain_instance
            entity_map: dict[tuple[type, str | None], Any] = {}

            # Handle positional arguments (no alias)
            for entity in entities:
                entity_type = type(entity)
                entity_map[(entity_type, None)] = entity

            # Handle named arguments (with alias)
            for alias_name, entity in named_entities.items():
                entity_type = type(entity)
                entity_map[(entity_type, alias_name)] = entity

            # Extract data using field mappings
            mapped_data = {}

            if hasattr(cls, "__field_mappings__") and cls.__field_mappings__:
                for view_field, (
                    domain_cls,
                    domain_field,
                    field_alias,
                ) in cls.__field_mappings__.items():
                    key = (domain_cls, field_alias)
                    if key in entity_map:
                        entity = entity_map[key]
                        entity_data = entity.model_dump()
                        if domain_field in entity_data:
                            mapped_data[view_field] = entity_data[domain_field]
                    else:
                        # Try without alias as fallback for non-aliased references
                        key_no_alias = (domain_cls, None)
                        if key_no_alias in entity_map:
                            entity = entity_map[key_no_alias]
                            entity_data = entity.model_dump()
                            if domain_field in entity_data:
                                mapped_data[view_field] = entity_data[domain_field]
                        else:
                            # Last resort: find any entity of this domain class
                            for (entity_cls, _), entity in entity_map.items():
                                if entity_cls == domain_cls:
                                    entity_data = entity.model_dump()
                                    if domain_field in entity_data:
                                        mapped_data[view_field] = entity_data[
                                            domain_field
                                        ]
                                    break

            # Add any unmapped fields by trying each entity
            for field_name in cls.model_fields:
                if field_name not in mapped_data:
                    # Try all entities
                    for entity in list(entities) + list(named_entities.values()):
                        entity_data = entity.model_dump()
                        if field_name in entity_data:
                            mapped_data[field_name] = entity_data[field_name]
                            break

            return cls(**mapped_data)

        else:
            # Single domain - legacy behavior
            if len(entities) != 1 or named_entities:
                raise ValueError(
                    f"{cls.__name__} expects exactly 1 positional domain instance, "
                    f"got {len(entities)} positional and {len(named_entities)} named"
                )

            entity = entities[0]

            # If we have field mappings, remap the data
            if hasattr(cls, "__field_mappings__") and cls.__field_mappings__:
                domain_data = entity.model_dump()
                mapped_data = {}

                # For single domain, field_mappings are (domain_class, field_name, alias)
                for view_field, mapping in cls.__field_mappings__.items():
                    if isinstance(mapping, tuple):
                        # New format: (domain_class, field_name, alias)
                        if len(mapping) == 3:
                            _, domain_field, _ = mapping
                        else:
                            # Backward compat: (domain_class, field_name)
                            _, domain_field = mapping
                    else:
                        # Old format: just field_name string (should not happen with new metaclass)
                        domain_field = mapping

                    if domain_field in domain_data:
                        mapped_data[view_field] = domain_data[domain_field]

                # Add any other fields that weren't explicitly mapped
                for field_name in cls.model_fields:
                    if field_name not in mapped_data and field_name in domain_data:
                        mapped_data[field_name] = domain_data[field_name]

                return cls(**mapped_data)
            else:
                return cls(**entity.model_dump())


class BuildDTO[D](BaseModel, metaclass=DTOMeta):
    """
    Base class for constructing Domain models from external data (inbound data flow).

    BuildDTO represents the minimal set of data required to construct a Domain
    entity from external sources (e.g., API requests, database records). It provides:
    1. Input validation and type coercion from external systems
    2. A clean interface for inbound data transformations
    3. Separation between external data contracts and internal Domain models

    Type Parameters:
        D: The Domain class this DTO will construct

    Usage:
        >>> class User(Domain):
        ...     id: int
        ...     username: str
        ...     email: str
        >>>
        >>> class CreateUser(BuildDTO[User]):
        ...     username: str
        ...     email: str
        >>>
        >>> dto = CreateUser(username="alice", email="alice@example.com")
        >>> def generate_user(create_user: CreateUser) -> User:
        ...     return User(**create_user.model_dump(), id=generate_id())
        >>>
        >>> user = generate_user(dto)
        >>> print(user.username)  # "alice"

    Attributes:
        __field_mappings__: Dictionary mapping DTO field names to Domain field names
    """
