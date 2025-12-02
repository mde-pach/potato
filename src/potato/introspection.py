from typing import Any, Annotated, get_type_hints, get_origin, get_args
from .types import FieldProxy

def extract_field_mappings(cls: type) -> dict[str, tuple[type, str, str | None]]:
    """
    Extract field mappings from Annotated types with FieldProxy metadata.

    Scans the class's type hints for Annotated[type, FieldProxy] patterns
    and builds a mapping of field names to (domain_class, field_name, alias) tuples.
    This enables the build() method to automatically extract values from
    referenced domain fields, supporting both single and aliased domain instances.

    Args:
        cls: The class being processed (Domain or ViewDTO)

    Returns:
        A dictionary mapping field names to (domain_class, domain_field_name, alias) tuples.
    """
    field_mappings: dict[str, tuple[type, str, str | None]] = {}
    
    # 1. Process Potato Fields (Field(source=...)) - mostly for ViewDTO
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

    # 2. Process Annotated types
    try:
        type_hints = get_type_hints(cls, include_extras=True)
        for field_name, field_type in type_hints.items():
            # Skip class variables and private attributes
            if field_name.startswith("_") or field_name in field_mappings:
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

    return field_mappings

def validate_aliases(
    cls: type,
    domain_aliases: dict[Any, list[Any | None]],
    field_mappings: dict[str, tuple[Any, str, Any | None]],
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

def get_aggregate_domain_types(cls: type) -> tuple[list[Any], dict[Any, list[Any | None]]]:
    """
    Extract aggregate domain types and aliases from a class (Domain or ViewDTO).
    
    Returns:
        A tuple containing:
        - list of domain types
        - dict mapping domain type to list of aliases
    """
    domain_aliases: dict[Any, list[Any | None]] = {}
    aggregate_domain_types: list[Any] = []
    aggregate_args: tuple[Any, ...] | None = None

    # Check for Pydantic generic metadata (Domain)
    if hasattr(cls, "__pydantic_generic_metadata__"):
        metadata = cls.__pydantic_generic_metadata__ # type: ignore
        if "args" in metadata and metadata["args"]:
            first_arg = metadata["args"][0]
            aggregate_origin = get_origin(first_arg)
            if aggregate_origin is not None:
                aggregate_args = get_args(first_arg)
                if aggregate_args:
                    for domain_spec in aggregate_args:
                        _process_domain_spec(domain_spec, aggregate_domain_types, domain_aliases)
                        
    # Check for Potato generic args (ViewDTO)
    for base in cls.__bases__:
        if hasattr(base, "__potato_generic_args__"):
            args = base.__potato_generic_args__
            if args:
                first_arg = args[0]
                
                # Check if first_arg is an Aggregate instance or type
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
                        _process_domain_spec(domain_spec, aggregate_domain_types, domain_aliases)
                    break

    return aggregate_domain_types, domain_aliases

def _process_domain_spec(domain_spec: Any, aggregate_domain_types: list, domain_aliases: dict):
    if hasattr(domain_spec, "_domain_cls") and hasattr(domain_spec, "_alias"):
        domain_type = domain_spec._domain_cls
        alias = domain_spec._alias
    else:
        domain_type = domain_spec
        alias = None

    aggregate_domain_types.append(domain_type)

    if domain_type not in domain_aliases:
        domain_aliases[domain_type] = []
    domain_aliases[domain_type].append(alias)
