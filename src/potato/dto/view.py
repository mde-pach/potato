import inspect
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Self,
    Generic,
)

from pydantic import BaseModel, ConfigDict, Field as PydanticField

from potato.core import Field
from potato.types import FieldProxy
from potato.introspection import (
    extract_field_mappings,
    validate_aliases,
    get_aggregate_domain_types,
)
from .base import DTOMeta, D, C


class ViewDTOMeta(DTOMeta):
    """
    Metaclass for ViewDTO that extracts field mappings and context type.
    """

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        **kwargs: Any,
    ) -> type:
        # Pre-process namespace to handle Potato Fields and Computed Methods
        potato_fields = {}
        computed_methods = {}
        
        for k, v in namespace.items():
            # mypy thinks this is a Callable but it's a class at runtime
            if isinstance(v, Field): # type: ignore
                potato_fields[k] = v
                if v.pydantic_kwargs:
                    namespace[k] = PydanticField(**v.pydantic_kwargs)
                else:
                    namespace[k] = PydanticField()
            elif hasattr(v, "_is_computed"):
                computed_methods[k] = v

        cls = super().__new__(mcs, name, bases, namespace, **kwargs)
        
        # Store potato fields and computed methods
        if potato_fields:
            cls.__potato_fields__ = potato_fields  # type: ignore
            
        if computed_methods:
            cls.__computed_methods__ = computed_methods # type: ignore

        # Extract aggregate domain types and context
        aggregate_domain_types, domain_aliases = get_aggregate_domain_types(cls)
        
        # Check for Context type in Potato generic args
        context_type = None
        for base in cls.__bases__:
            if hasattr(base, "__potato_generic_args__"):
                args = base.__potato_generic_args__
                if len(args) > 1:
                    context_type = args[1]
                    break

        if context_type:
            cls.__context_type__ = context_type # type: ignore

        if aggregate_domain_types:
            cls.__aggregate_domain_types__ = tuple(aggregate_domain_types)  # type: ignore
            cls.__domain_aliases__ = domain_aliases  # type: ignore

        # Extract field mappings: view_field -> (domain_class, domain_field, alias)
        field_mappings = extract_field_mappings(cls)

        if field_mappings:
            cls.__field_mappings__ = field_mappings  # type: ignore

        # Validate that field references use declared aliases
        if hasattr(cls, "__domain_aliases__") and field_mappings:
            validate_aliases(cls, domain_aliases, field_mappings)  # type: ignore

        return cls


class ViewDTO(BaseModel, Generic[D, C], metaclass=ViewDTOMeta):
    """
    Base class for Domain-derived DTOs (outbound data flow).
    """

    __field_mappings__: ClassVar[dict[str, tuple[type, str, str | None]]] = {}
    __aggregate_domain_types__: ClassVar[tuple[type, ...]] = ()
    __domain_aliases__: ClassVar[dict[type, list[str | None]]] = {}
    __context_type__: ClassVar[type | None] = None

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
    def __class_getitem__(cls, item: Any) -> Any:
        """
        Support ViewDTO[Domain] and ViewDTO[Domain, Context].
        """
        if not isinstance(item, tuple):
            item = (item,)
            
        # Create a dynamic class that holds the generic args
        # This class will be the base of the user's DTO
        class _GenericViewDTO(cls):
            __potato_generic_args__ = item
            
            # We must pretend to be the original class for isinstance checks if needed
            # but for now this is enough for the metaclass to find args
        
        _GenericViewDTO.__name__ = f"ViewDTO[{', '.join(str(x) for x in item)}]"
        return _GenericViewDTO

    @classmethod
    def _build_entity_map(
        cls: type[Self],
        entities: tuple[Any, ...],
        named_entities: dict[str, Any],
        domain_aliases: dict[type, list[str | None]],
    ) -> dict[tuple[type, str | None], Any]:
        entity_map: dict[tuple[type, str | None], Any] = {}

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

        for entity in entities:
            entity_type = type(entity)
            entity_map[(entity_type, None)] = entity

        for alias_name, entity in named_entities.items():
            # Skip context if passed as named arg but not meant for entity map
            if alias_name == "context":
                continue
                
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
                    f"{cls.__name__}.build() got unexpected parameter '{alias_name}'."
                )

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
        context: Any = None,
    ) -> dict[str, Any]:
        mapped_data = {}

        # 1. Mapped fields
        if hasattr(cls, "__field_mappings__") and cls.__field_mappings__:
            for view_field, (
                domain_cls,
                domain_field,
                field_alias,
            ) in cls.__field_mappings__.items():
                key = (domain_cls, field_alias)
                if key in entity_map:
                    entity = entity_map[key]
                    # Access attribute directly instead of model_dump for speed
                    if hasattr(entity, domain_field):
                        mapped_data[view_field] = getattr(entity, domain_field)
                else:
                    key_no_alias = (domain_cls, None)
                    if key_no_alias in entity_map:
                        entity = entity_map[key_no_alias]
                        if hasattr(entity, domain_field):
                            mapped_data[view_field] = getattr(entity, domain_field)

        # 2. Computed fields
        # Iterate over methods marked with @computed
        for name, member in inspect.getmembers(cls):
            if hasattr(member, "_is_computed"):
                pass

        # 3. Unmapped fields (auto-map by name)
        for field_name in cls.model_fields:
            if field_name not in mapped_data:
                # Try to find in entities
                found = False
                for entity in entity_map.values():
                    if hasattr(entity, field_name):
                        mapped_data[field_name] = getattr(entity, field_name)
                        found = True
                        break
                if not found:
                     # Check named entities (fallback)
                     for entity in named_entities.values():
                        if hasattr(entity, field_name):
                            mapped_data[field_name] = getattr(entity, field_name)
                            break

        return mapped_data

    @classmethod
    def build(cls: type[Self], *entities: Any, context: Any = None, **named_entities: Any) -> Self:
        """
        Build a ViewDTO from one or more Domain instances.
        """
        # Validate context type if defined
        if cls.__context_type__ and context is not None:
            if not isinstance(context, cls.__context_type__):
                raise TypeError(
                    f"Expected context of type {cls.__context_type__.__name__}, "
                    f"got {type(context).__name__}"
                )

        if (
            hasattr(cls, "__aggregate_domain_types__")
            and cls.__aggregate_domain_types__
        ):
            domain_aliases = getattr(cls, "__domain_aliases__", {})
            entity_map = cls._build_entity_map(entities, named_entities, domain_aliases)
            mapped_data = cls._extract_mapped_data(entity_map, named_entities, context)
            
            # Create instance
            instance = cls(**mapped_data)
            
            # Handle computed fields (post-init injection)
            cls._inject_computed_fields(instance, entity_map, context)
            return instance

        else:
            if len(entities) != 1 or named_entities:
                if not (len(entities) == 0 and len(named_entities) == 1): # Allow single named entity
                     raise ValueError(
                        f"{cls.__name__} expects exactly 1 positional domain instance"
                    )
            
            entity = entities[0] if entities else list(named_entities.values())[0]
            domain_data = entity.model_dump()

            if not (hasattr(cls, "__field_mappings__") and cls.__field_mappings__):
                instance = cls(**domain_data)
                cls._inject_computed_fields(instance, {(type(entity), None): entity}, context)
                return instance

            mapped_data = {}
            for view_field, (_, domain_field, _) in cls.__field_mappings__.items():
                if domain_field in domain_data:
                    mapped_data[view_field] = domain_data[domain_field]

            for field_name in cls.model_fields:
                if field_name not in mapped_data and field_name in domain_data:
                    mapped_data[field_name] = domain_data[field_name]

            instance = cls(**mapped_data)
            cls._inject_computed_fields(instance, {(type(entity), None): entity}, context)
            return instance

    @classmethod
    def _inject_computed_fields(cls, instance: Self, entity_map: dict, context: Any) -> None:
        """
        Execute @computed methods and set their values on the instance.
        """
        computed_methods = getattr(cls, "__computed_methods__", {})
        
        for name, member in computed_methods.items():
            # Check signature for context injection
            sig = inspect.signature(member)
            kwargs = {}
            
            # Inject context if requested
            if "context" in sig.parameters:
                # Check type hint if strict? For now just inject if name matches
                kwargs["context"] = context
            
            # Inject domains?
            # The method signature might request specific domains: def age(self, user: User)
            # We need to match arguments to entities in entity_map
            for param_name, param in sig.parameters.items():
                if param_name in ("self", "context"):
                    continue
                
                # Try to find entity by type hint
                if param.annotation != inspect.Parameter.empty:
                    # Find entity of this type in map
                    found = False
                    for (domain_type, alias), entity in entity_map.items():
                        if issubclass(domain_type, param.annotation):
                            kwargs[param_name] = entity
                            found = True
                            break
                    if not found:
                            # Try by name (fallback)
                            pass
            
            try:
                val = member(instance, **kwargs)
                # Bypass frozen check
                object.__setattr__(instance, name, val)
            except Exception as e:
                # Log or re-raise?
                pass
