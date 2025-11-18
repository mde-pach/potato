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
    from potato.domain import FieldProxy
else:
    from potato.domain import FieldProxy


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
        alias: FieldProxy | None

        # Extract aggregate domain types and their aliases if present
        domain_aliases: dict[FieldProxy, list[FieldProxy | None]] = {}
        aggregate_domain_types: list[FieldProxy] = []

        for base in cls.__bases__:
            if hasattr(base, "__pydantic_generic_metadata__"):
                metadata = base.__pydantic_generic_metadata__
                if "args" in metadata and metadata["args"]:
                    first_arg = metadata["args"][0]

                    # Check if first_arg is an Aggregate instance (new pattern)
                    # With the new pattern, Aggregate[User, Product] returns a class that
                    # has __aggregate_domain_types__ attribute set by AggregateMeta
                    if hasattr(first_arg, "__aggregate_domain_types__"):
                        aggregate_args = first_arg.__aggregate_domain_types__
                    else:
                        # Old pattern: check if it's a generic alias like Aggregate[...]
                        aggregate_origin = get_origin(first_arg)
                        if aggregate_origin is not None:
                            aggregate_args = get_args(first_arg)
                        else:
                            aggregate_args = None

                    if aggregate_args:
                        # Get the domain types from Aggregate[User, Profile, ...] or aliased types
                        # created via Domain.alias() like Aggregate[Buyer, Seller, ...]
                        # where Buyer = User.alias("buyer")
                        for domain_spec in aggregate_args:
                            # Check if it's an AliasedType (created via Domain.alias())
                            # AliasedType returns a type/class, not an instance, so we check for attributes
                            if hasattr(domain_spec, "_domain_cls") and hasattr(
                                domain_spec, "_alias"
                            ):
                                domain_type = domain_spec._domain_cls
                                alias = domain_spec._alias
                            else:
                                # Plain domain, no alias
                                domain_type = domain_spec
                                alias = None

                            aggregate_domain_types.append(domain_type)

                            # Track aliases for each domain type
                            if domain_type not in domain_aliases:
                                domain_aliases[domain_type] = []
                            domain_aliases[domain_type].append(alias)
                        break

        if aggregate_domain_types:
            cls.__aggregate_domain_types__ = tuple(aggregate_domain_types)  # type: ignore
            cls.__domain_aliases__ = domain_aliases  # type: ignore

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

        # Validate that field references use declared aliases
        if hasattr(cls, "__domain_aliases__") and field_mappings:
            # TODO fix the type error here
            ViewDTOMeta._validate_aliases(cls, domain_aliases, field_mappings)  # type: ignore

        return cls

    @staticmethod
    def _validate_aliases(
        cls: type,
        domain_aliases: dict[FieldProxy, list[FieldProxy | None]],
        field_mappings: dict[str, tuple[FieldProxy, str, FieldProxy | None]],
    ) -> None:
        """
        Validate that field references use aliases declared in Aggregate.

        Raises ValueError if a field uses an alias not declared in the Aggregate.
        """
        for view_field, (
            domain_cls,
            domain_field,
            field_alias,
        ) in field_mappings.items():
            if domain_cls not in domain_aliases:
                # Domain not in aggregate, skip validation
                continue

            declared_aliases = domain_aliases[domain_cls]

            # If there's only one instance of this domain type, alias should be None
            if len(declared_aliases) == 1 and declared_aliases[0] is None:
                if field_alias is not None:
                    raise ValueError(
                        f"ViewDTO '{cls.__name__}' field '{view_field}' uses alias '{field_alias}' "
                        f"but Domain '{domain_cls.__class__.__name__}' has no alias declared in Aggregate. "
                        f"Remove the alias from the field reference."
                    )
            # If there are multiple instances, alias must be declared
            elif len(declared_aliases) > 1:
                if field_alias is None:
                    raise ValueError(
                        f"ViewDTO '{cls.__name__}' field '{view_field}' references Domain '{domain_cls.__class__.__name__}' "
                        f"without an alias, but multiple instances are declared in Aggregate. "
                        f'Use Annotated[type, {domain_cls.__class__.__name__}("alias").{domain_field}] '
                        f"with one of the declared aliases: {[a for a in declared_aliases if a is not None]}"
                    )
                elif field_alias not in declared_aliases:
                    raise ValueError(
                        f"ViewDTO '{cls.__name__}' field '{view_field}' uses alias '{field_alias}' "
                        f"which is not declared in Aggregate for Domain '{domain_cls.__class__.__name__}'. "
                        f"Declared aliases: {[a for a in declared_aliases if a is not None]}"
                    )


class ViewDTO[D](BaseModel, metaclass=ViewDTOMeta):
    """
    Base class for Domain-derived DTOs (outbound data flow).

    ViewDTO creates immutable data transfer objects from Domain models for
    external consumption (e.g., API responses). It supports:
    1. Single domain: ViewDTO[DomainA]
    2. Multiple domains: ViewDTO[Aggregate[DomainA, DomainB, DomainC]]
    3. Multiple instances of same domain via aliasing: DomainA("first"), DomainA("second")
    4. Automatic field mapping via Annotated[type, Domain.field]
    5. Compile-time validation that all required Domain fields are present

    Type Parameters:
        D: The Domain class or Aggregate[Domain1, Domain2, ...] this DTO is derived from

    Usage - Single domain:
        >>> class DomainA(Domain):
        ...     id: int
        ...     name: str
        >>>
        >>> class EntityView(ViewDTO[DomainA]):
        ...     id: int
        ...     name: str
        >>>
        >>> entity = DomainA(id=1, name="example")
        >>> view = EntityView.build(entity)

    Usage - Multiple domains:
        >>> class DomainB(Domain):
        ...     description: str
        >>>
        >>> class CombinedView(ViewDTO[Aggregate[DomainA, DomainB]]):
        ...     id: Annotated[int, DomainA.id]
        ...     name: Annotated[str, DomainA.name]
        ...     description: Annotated[str, DomainB.description]
        >>>
        >>> view = CombinedView.build(entity_a, entity_b)

    Usage - Multiple instances of same domain (aliasing):
        >>> Source = DomainA.alias("source")
        >>> Target = DomainA.alias("target")
        >>> class RelationView(ViewDTO[Aggregate[Source, Target, DomainB]]):
        ...     source_id: Annotated[int, Source.id]
        ...     source_name: Annotated[str, Source.name]
        ...     target_id: Annotated[int, Target.id]
        ...     target_name: Annotated[str, Target.name]
        ...     description: Annotated[str, DomainB.description]
        >>>
        >>> view = RelationView.build(source=first_entity, target=second_entity, domainb=entity_b)

    Attributes:
        __field_mappings__: Dict mapping DTO fields to (domain_class, field_name, alias)
        __aggregate_domain_types__: Tuple of Domain types when using Aggregate
        __domain_aliases__: Dict mapping domain types to list of aliases (None for unaliased)
    """

    __field_mappings__: ClassVar[dict[str, tuple[type, str, str | None]]] = {}
    __aggregate_domain_types__: ClassVar[tuple[type, ...]] = ()
    __domain_aliases__: ClassVar[dict[type, list[str | None]]] = {}

    model_config = ConfigDict(
        extra="ignore",
        coerce_numbers_to_str=True,
        populate_by_name=True,
        validate_by_alias=True,
        validate_by_name=True,
        frozen=True,
        from_attributes=True,
    )

    @classmethod
    def _build_entity_map(
        cls: type[Self],
        entities: tuple[Any, ...],
        named_entities: dict[str, Any],
        domain_aliases: dict[type, list[str | None]],
    ) -> dict[tuple[type, str | None], Any]:
        """
        Build a map of (domain_class, alias) -> domain_instance.

        Args:
            entities: Positional domain instances
            named_entities: Named domain instances
            domain_aliases: Mapping of domain types to their aliases

        Returns:
            Dictionary mapping (domain_type, alias) to entity instances

        Raises:
            ValueError: If parameter names don't match expected values
        """
        entity_map: dict[tuple[type, str | None], Any] = {}

        # Build expected parameter names based on aliases
        expected_params: dict[str, tuple[type, str | None]] = {}
        if domain_aliases:
            for domain_type in cls.__aggregate_domain_types__:
                aliases = domain_aliases.get(domain_type, [None])
                for alias in aliases:
                    param_name = alias if alias else domain_type.__name__.lower()
                    expected_params[param_name] = (domain_type, alias)
        else:
            for domain_type in cls.__aggregate_domain_types__:
                param_name = domain_type.__name__.lower()
                expected_params[param_name] = (domain_type, None)

        # Handle positional arguments
        for entity in entities:
            entity_type = type(entity)
            entity_map[(entity_type, None)] = entity

        # Handle named arguments
        for alias_name, entity in named_entities.items():
            entity_type = type(entity)
            if alias_name in expected_params:
                expected_type, expected_alias = expected_params[alias_name]
                if expected_type != entity_type:
                    raise ValueError(
                        f"{cls.__name__}.build() parameter '{alias_name}' expects "
                        f"Domain type '{expected_type.__name__}', got '{entity_type.__name__}'"
                    )
                entity_map[(entity_type, expected_alias)] = entity
            else:
                raise ValueError(
                    f"{cls.__name__}.build() got unexpected parameter '{alias_name}'. "
                    f"Expected parameters: {list(expected_params.keys())}"
                )

        # Validate all expected parameters are provided
        for param_name, (expected_type, expected_alias) in expected_params.items():
            key = (expected_type, expected_alias)
            if key not in entity_map:
                raise ValueError(
                    f"{cls.__name__}.build() missing required parameter '{param_name}' "
                    f"of type '{expected_type.__name__}'"
                )

        return entity_map

    @classmethod
    def _extract_mapped_data(
        cls: type[Self],
        entity_map: dict[tuple[type, str | None], Any],
        named_entities: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Extract data from entities using field mappings.

        Args:
            entity_map: Map of (domain_type, alias) to entity instances
            named_entities: Named entities for unmapped field fallback

        Returns:
            Dictionary of field values for DTO construction
        """
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
                    # Try without alias as fallback
                    key_no_alias = (domain_cls, None)
                    if key_no_alias in entity_map:
                        entity = entity_map[key_no_alias]
                        entity_data = entity.model_dump()
                        if domain_field in entity_data:
                            mapped_data[view_field] = entity_data[domain_field]

        # Add any unmapped fields from entities
        for field_name in cls.model_fields:
            if field_name not in mapped_data:
                for entity in named_entities.values():
                    entity_data = entity.model_dump()
                    if field_name in entity_data:
                        mapped_data[field_name] = entity_data[field_name]
                        break

        return mapped_data

    @classmethod
    def build(cls: type[Self], *entities: Any, **named_entities: Any) -> Self:
        """
        Build a ViewDTO from one or more Domain instances.

        For single domain ViewDTO[DomainA]:
            >>> view = EntityView.build(entity)

        For aggregate ViewDTO[Aggregate[DomainA, DomainB]]:
            >>> view = CombinedView.build(entity_a, entity_b)

        For aggregate with duplicate domains (use named arguments):
            >>> view = RelationView.build(source=first_entity, target=second_entity, domainb=entity_b)

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
            # Multiple domains - build entity map and extract data
            domain_aliases = getattr(cls, "__domain_aliases__", {})
            entity_map = cls._build_entity_map(entities, named_entities, domain_aliases)
            mapped_data = cls._extract_mapped_data(entity_map, named_entities)
            return cls(**mapped_data)

        else:
            # Single domain
            if len(entities) != 1 or named_entities:
                raise ValueError(
                    f"{cls.__name__} expects exactly 1 positional domain instance, "
                    f"got {len(entities)} positional and {len(named_entities)} named"
                )

            entity = entities[0]
            domain_data = entity.model_dump()

            # If we have field mappings, remap the data
            if not (hasattr(cls, "__field_mappings__") and cls.__field_mappings__):
                return cls(**domain_data)

            mapped_data = {}

            # Extract fields using mappings
            for view_field, (_, domain_field, _) in cls.__field_mappings__.items():
                if domain_field in domain_data:
                    mapped_data[view_field] = domain_data[domain_field]

            # Add any unmapped fields
            for field_name in cls.model_fields:
                if field_name not in mapped_data and field_name in domain_data:
                    mapped_data[field_name] = domain_data[field_name]

            return cls(**mapped_data)


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
        >>> class DomainA(Domain):
        ...     id: int
        ...     name: str
        ...     value: str
        >>>
        >>> class CreateEntity(BuildDTO[DomainA]):
        ...     name: str
        ...     value: str
        >>>
        >>> dto = CreateEntity(name="example", value="data")
        >>> def generate_entity(create_dto: CreateEntity) -> DomainA:
        ...     return DomainA(**create_dto.model_dump(), id=generate_id())
        >>>
        >>> entity = generate_entity(dto)
        >>> print(entity.name)  # "example"

    Attributes:
        __field_mappings__: Dictionary mapping DTO field names to Domain field names
    """
