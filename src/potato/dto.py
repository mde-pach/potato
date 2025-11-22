"""
DTO module - Data Transfer Objects for unidirectional data flow.

This module provides ViewDTO and BuildDTO base classes that enable type-safe
data transformations between Domain models and external representations.

The DTOs enforce a unidirectional data flow:
- BuildDTO: External data → Domain (inbound)
- ViewDTO: Domain → External data (outbound)
"""

import inspect
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
    Generic,
    TypeVar,
)

from pydantic import BaseModel, ConfigDict, Field as PydanticField
from pydantic._internal._model_construction import (
    ModelMetaclass,
    NoInitField,
    PydanticModelField,
    PydanticModelPrivateAttr,
)

from potato.core import Field, SystemMarker

if TYPE_CHECKING:
    from potato.domain import FieldProxy
else:
    from potato.domain import FieldProxy

D = TypeVar("D")
C = TypeVar("C", default=None)

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
            if isinstance(v, Field):
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

        alias: FieldProxy | None
        
        # Extract aggregate domain types and context
        domain_aliases: dict[FieldProxy, list[FieldProxy | None]] = {}
        aggregate_domain_types: list[FieldProxy] = []
        context_type = None

        for base in cls.__bases__:
            # Check for Potato generic args (custom implementation)
            if hasattr(base, "__potato_generic_args__"):
                args = base.__potato_generic_args__
                if args:
                    first_arg = args[0]
                    
                    # Check for Context type (second argument)
                    if len(args) > 1:
                        context_type = args[1]

                    # Check if first_arg is an Aggregate instance
                    if hasattr(first_arg, "__aggregate_domain_types__"):
                        aggregate_args = first_arg.__aggregate_domain_types__
                    else:
                        aggregate_origin = get_origin(first_arg)
                        if aggregate_origin is not None:
                            aggregate_args = get_args(first_arg)
                        else:
                            aggregate_args = None

                    if aggregate_args:
                        for domain_spec in aggregate_args:
                            if hasattr(domain_spec, "_domain_cls") and hasattr(
                                domain_spec, "_alias"
                            ):
                                domain_type = domain_spec._domain_cls
                                alias = domain_spec._alias
                            else:
                                domain_type = domain_spec
                                alias = None

                            aggregate_domain_types.append(domain_type)

                            if domain_type not in domain_aliases:
                                domain_aliases[domain_type] = []
                            domain_aliases[domain_type].append(alias)
                        break
            
            # Fallback to Pydantic generic metadata (if we ever use standard Generic)
            elif hasattr(base, "__pydantic_generic_metadata__"):
                 # ... (existing logic if needed, but we are replacing it)
                 pass
        
        if context_type:
            cls.__context_type__ = context_type # type: ignore

        if aggregate_domain_types:
            cls.__aggregate_domain_types__ = tuple(aggregate_domain_types)  # type: ignore
            cls.__domain_aliases__ = domain_aliases  # type: ignore

        # Extract field mappings: view_field -> (domain_class, domain_field, alias)
        field_mappings: dict[str, tuple[type, str, str | None]] = {}
        
        # 1. Process Potato Fields (Field(source=...))
        if hasattr(cls, "__potato_fields__"):
            for field_name, field_def in cls.__potato_fields__.items(): # type: ignore
                if field_def.source:
                    # source should be a FieldProxy
                    if isinstance(field_def.source, FieldProxy):
                        field_mappings[field_name] = (
                            field_def.source.model_cls,
                            field_def.source.field_name,
                            field_def.source.alias,
                        )
        
        # 2. Process Annotated types (Legacy/Alternative)
        try:
            type_hints = get_type_hints(cls, include_extras=True)
            for field_name, field_type in type_hints.items():
                if field_name.startswith("_") or field_name in field_mappings:
                    continue

                origin = get_origin(field_type)
                if origin is Annotated:
                    args = get_args(field_type)
                    for metadata in args[1:]:
                        if isinstance(metadata, FieldProxy):
                            field_mappings[field_name] = (
                                metadata.model_cls,
                                metadata.field_name,
                                metadata.alias,
                            )
                            break
        except Exception:
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
                # It's a computed field. We need to call it.
                # But we can't call unbound method easily on class.
                # We need to instantiate the DTO first? No, DTO is immutable.
                # We need to compute values BEFORE instantiation.
                # But the method is on the class (or instance).
                # If it's on the class, it expects 'self'.
                # This implies computed fields must be calculated AFTER instantiation?
                # But ViewDTO is frozen.
                # Solution: Computed fields should be calculated and passed to constructor?
                # OR ViewDTO allows computing properties?
                # Pydantic @computed_field works on instance.
                # But our @computed is custom.
                # Let's assume for now we calculate them here and pass to constructor?
                # No, methods need 'self'.
                # If they need 'self', they run on the instance.
                # Pydantic's @computed_field is what we want behavior-wise.
                # But we want to inject context.
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
            # We iterate over computed methods and set the values?
            # But model is frozen.
            # We should use Pydantic's model_post_init or similar?
            # Or just calculate them and use object.__setattr__ since it's frozen.
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


class BuildDTO(BaseModel, Generic[D], metaclass=DTOMeta):
    """
    Base class for constructing Domain models from external data (inbound data flow).
    """
    
    @classmethod
    def __class_getitem__(cls, item: Any) -> Any:
        """
        Support BuildDTO[Domain].
        """
        if not isinstance(item, tuple):
            item = (item,)
            
        class _GenericBuildDTO(cls):
            __potato_generic_args__ = item
            
        _GenericBuildDTO.__name__ = f"BuildDTO[{', '.join(str(x) for x in item)}]"
        return _GenericBuildDTO

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        super().__pydantic_init_subclass__(**kwargs)
        
        # Extract the Domain type D
        domain_cls = None
        # Check Potato generic args
        if hasattr(cls, "__potato_generic_args__"):
            args = cls.__potato_generic_args__
            if args:
                domain_cls = args[0]
        
        if domain_cls:
            cls._domain_cls = domain_cls

    def to_domain(self, **kwargs: Any) -> Self._domain_cls:
        """
        Convert the DTO to a Domain instance.
        
        Args:
            **kwargs: Additional fields required by the Domain (e.g., System fields like id)
            
        Returns:
            An instance of the Domain class D
        """
        if not hasattr(self, "_domain_cls") or not self._domain_cls:
            raise ValueError("BuildDTO must have a Domain type argument (e.g. BuildDTO[User])")
            
        # Combine DTO data with kwargs
        data = self.model_dump()
        data.update(kwargs)
        
        return self._domain_cls(**data)
