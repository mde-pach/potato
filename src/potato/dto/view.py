import asyncio
import inspect
import types
import typing
from typing import (
    Any,
    ClassVar,
    Generic,
    Self,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

from pydantic import BaseModel, ConfigDict
from pydantic import Field as PydanticField

from potato.core import AutoMarker, Field, PrivateMarker
from potato.introspection import extract_field_mappings
from potato.types import FieldProxy

from .base import C, D, DTOMeta


def _is_auto_field(field_type: Any) -> bool:
    """Check if a type is Auto[T] (has AutoMarker in metadata)."""
    from typing import Annotated
    if get_origin(field_type) is Annotated:
        for meta in get_args(field_type)[1:]:
            if isinstance(meta, AutoMarker) or meta is AutoMarker:
                return True
    return False


def _is_private_field(field_type: Any) -> bool:
    """Check if a type is Private[T] (has PrivateMarker in metadata)."""
    from typing import Annotated
    if get_origin(field_type) is Annotated:
        for meta in get_args(field_type)[1:]:
            if isinstance(meta, PrivateMarker) or meta is PrivateMarker:
                return True
    return False


def _is_viewdto_type(tp: Any) -> bool:
    """Check if a type is a ViewDTO subclass."""
    try:
        if isinstance(tp, type) and issubclass(tp, ViewDTO):
            return True
    except TypeError:
        pass
    return False


def _unwrap_list_type(tp: Any) -> tuple[bool, Any]:
    """If tp is list[X], return (True, X). Otherwise (False, tp)."""
    origin = get_origin(tp)
    if origin is list:
        args = get_args(tp)
        if args:
            return True, args[0]
    return False, tp


def _is_optional_context_type(context_type: Any) -> tuple[bool, Any]:
    """
    Check if a context type is optional (union with NoneType).

    Returns (is_optional, unwrapped_type).
    If optional, unwrapped_type is the non-None type from the union.
    """
    origin = get_origin(context_type)
    # Check for types.UnionType (X | Y) and typing.Union
    if origin is Union or isinstance(context_type, types.UnionType):
        args = get_args(context_type)
        non_none = [a for a in args if a is not type(None)]
        if type(None) in args and len(non_none) == 1:
            return True, non_none[0]
    return False, context_type


def _transform_wants_context(transform: Any) -> bool:
    """Check if a transform callable accepts 2+ positional parameters."""
    try:
        sig = inspect.signature(transform)
        positional_kinds = (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        )
        positional_count = sum(
            1 for p in sig.parameters.values()
            if p.kind in positional_kinds
        )
        return positional_count >= 2
    except (ValueError, TypeError):
        return False


def _build_hook_kwargs(sig: inspect.Signature, entity: Any, context: Any) -> dict[str, Any]:
    """Build kwargs dict for before_build/after_build hooks based on signature inspection."""
    hook_kwargs: dict[str, Any] = {}
    for param_name, param in sig.parameters.items():
        if param_name in ("cls", "self"):
            continue
        if param_name == "context":
            hook_kwargs["context"] = context
        elif param.annotation != inspect.Parameter.empty:
            if isinstance(entity, param.annotation):
                hook_kwargs[param_name] = entity
            elif hasattr(entity, "__aggregate_domain_fields__"):
                for field_name, domain_type in entity.__aggregate_domain_fields__.items():
                    sub_entity = getattr(entity, field_name, None)
                    if sub_entity is not None and isinstance(sub_entity, param.annotation):
                        hook_kwargs[param_name] = sub_entity
                        break
        else:
            hook_kwargs[param_name] = entity
    return hook_kwargs


class ViewDTOMeta(DTOMeta):
    """
    Metaclass for ViewDTO that extracts field mappings, context type,
    and validates field references at class definition time.
    """

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        **kwargs: Any,
    ) -> type:
        # Handle exclude parameter
        exclude = kwargs.pop("exclude", None)

        # Pre-process namespace to handle Potato Fields and Computed/Hook Methods
        potato_fields: dict[str, Field] = {}
        computed_methods: dict[str, Any] = {}
        before_build_hooks: list[Any] = []
        after_build_hooks: list[Any] = []

        annotations = namespace.get("__annotations__", {})

        for k, v in list(namespace.items()):
            if isinstance(v, Field):  # type: ignore
                potato_fields[k] = v
                if v.pydantic_kwargs:
                    namespace[k] = PydanticField(**v.pydantic_kwargs)
                else:
                    namespace[k] = PydanticField()
            elif hasattr(v, "_is_computed"):
                computed_methods[k] = v
            elif isinstance(v, classmethod) and hasattr(v.__func__, "_is_before_build"):
                before_build_hooks.append(v)
            elif hasattr(v, "_is_before_build"):
                before_build_hooks.append(v)
            elif hasattr(v, "_is_after_build"):
                after_build_hooks.append(v)

        cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        # Store metadata
        if potato_fields:
            cls.__potato_fields__ = potato_fields  # type: ignore

        if computed_methods:
            cls.__computed_methods__ = computed_methods  # type: ignore

        if before_build_hooks:
            cls.__before_build_hooks__ = before_build_hooks  # type: ignore

        if after_build_hooks:
            cls.__after_build_hooks__ = after_build_hooks  # type: ignore

        # Extract domain class and context type from generic args
        domain_cls = None
        context_type = None
        for base in cls.__bases__:
            if hasattr(base, "__potato_generic_args__"):
                args = base.__potato_generic_args__
                if args:
                    domain_cls = args[0]
                if len(args) > 1:
                    context_type = args[1]
                break

        if domain_cls:
            cls.__domain_cls__ = domain_cls  # type: ignore

        # Process context type: determine if required or optional
        if context_type:
            is_optional, unwrapped = _is_optional_context_type(context_type)
            cls.__context_type__ = unwrapped  # type: ignore
            cls.__context_required__ = not is_optional  # type: ignore
        else:
            cls.__context_required__ = False  # type: ignore

        # Inspect transforms for context acceptance
        for field_def in potato_fields.values():
            if field_def.transform:
                field_def._transform_wants_context = _transform_wants_context(field_def.transform)

        # Check if domain is an Aggregate (has __aggregate_domain_fields__)
        is_aggregate = hasattr(domain_cls, "__aggregate_domain_fields__") if domain_cls else False
        cls.__is_aggregate_view__ = is_aggregate  # type: ignore

        # Handle exclude parameter — auto-include remaining domain fields
        if exclude is not None and domain_cls is not None:
            _apply_exclude(cls, domain_cls, exclude, namespace)

        # Merge parent potato metadata for DTO inheritance
        _merge_parent_metadata(cls, bases)

        # Extract field mappings
        field_mappings = extract_field_mappings(cls)
        if field_mappings:
            cls.__field_mappings__ = field_mappings  # type: ignore

        # Validate field mappings
        if field_mappings and domain_cls:
            _validate_viewdto_field_mappings(cls, field_mappings, domain_cls)

        # Validate no Private fields are exposed
        if domain_cls:
            _validate_no_private_fields(cls, domain_cls)

        return cls


def _apply_exclude(cls: type, domain_cls: type, exclude: list, namespace: dict) -> None:
    """Auto-include all domain fields except excluded ones."""

    # Get excluded field names
    excluded_names: set[str] = set()
    for item in exclude:
        if isinstance(item, FieldProxy):
            excluded_names.add(item.field_name)
        elif isinstance(item, str):
            excluded_names.add(item)

    # Get domain field types
    try:
        domain_hints = get_type_hints(domain_cls)
    except Exception:
        return

    # Auto-include non-excluded fields (skip private and already-declared)
    existing_fields = set(cls.model_fields.keys()) if hasattr(cls, "model_fields") else set()
    annotations = getattr(cls, "__annotations__", {})

    for field_name, field_type in domain_hints.items():
        if field_name.startswith("_"):
            continue
        if field_name in excluded_names:
            continue
        if field_name in existing_fields or field_name in annotations:
            continue
        if _is_private_field(field_type):
            continue
        # Add auto-annotation
        annotations[field_name] = field_type

    cls.__annotations__ = annotations


def _merge_parent_metadata(cls: type, bases: tuple[type, ...]) -> None:
    """Merge parent ViewDTO's potato metadata with child's."""
    for base in bases:
        # Merge field mappings from parent
        parent_mappings = getattr(base, "__field_mappings__", {})
        child_mappings = getattr(cls, "__field_mappings__", {})
        if parent_mappings:
            merged = {**parent_mappings, **child_mappings}
            cls.__field_mappings__ = merged  # type: ignore

        # Merge computed methods from parent
        parent_computed = getattr(base, "__computed_methods__", {})
        child_computed = getattr(cls, "__computed_methods__", {})
        if parent_computed:
            merged_computed = {**parent_computed, **child_computed}
            cls.__computed_methods__ = merged_computed  # type: ignore

        # Merge potato fields from parent
        parent_potato = getattr(base, "__potato_fields__", {})
        child_potato = getattr(cls, "__potato_fields__", {})
        if parent_potato:
            merged_potato = {**parent_potato, **child_potato}
            cls.__potato_fields__ = merged_potato  # type: ignore

        # Inherit domain_cls if not set
        if not hasattr(cls, "__domain_cls__") and hasattr(base, "__domain_cls__"):
            cls.__domain_cls__ = base.__domain_cls__  # type: ignore

        # Inherit context_type if not set
        if not hasattr(cls, "__context_type__") and hasattr(base, "__context_type__"):
            cls.__context_type__ = base.__context_type__  # type: ignore

        # Inherit context_required if not set
        if not getattr(cls, "__context_required__", False) and getattr(base, "__context_required__", False):
            cls.__context_required__ = base.__context_required__  # type: ignore

        # Inherit is_aggregate_view if not set
        if not getattr(cls, "__is_aggregate_view__", False) and getattr(base, "__is_aggregate_view__", False):
            cls.__is_aggregate_view__ = base.__is_aggregate_view__  # type: ignore

        # Merge hooks
        parent_before = getattr(base, "__before_build_hooks__", [])
        child_before = getattr(cls, "__before_build_hooks__", [])
        if parent_before:
            cls.__before_build_hooks__ = parent_before + child_before  # type: ignore

        parent_after = getattr(base, "__after_build_hooks__", [])
        child_after = getattr(cls, "__after_build_hooks__", [])
        if parent_after:
            cls.__after_build_hooks__ = parent_after + child_after  # type: ignore


def _validate_viewdto_field_mappings(
    cls: type,
    field_mappings: dict[str, tuple[type, str, str | None, list[str]]],
    domain_cls: type,
) -> None:
    """Validate that ViewDTO field mappings reference correct domains and existing fields."""
    from potato.domain.aggregates import Aggregate

    is_aggregate = isinstance(domain_cls, type) and issubclass(domain_cls, Aggregate) and domain_cls is not Aggregate
    aggregate_domain_fields = getattr(domain_cls, "__aggregate_domain_fields__", {})

    if is_aggregate:
        # Allowed domain classes are those declared as Aggregate fields + the aggregate itself
        allowed_domain_classes: set[type] = set(aggregate_domain_fields.values())
        allowed_domain_classes.add(domain_cls)
    else:
        allowed_domain_classes = {domain_cls}

    for view_field, (ref_domain_cls, domain_field, namespace, path) in field_mappings.items():
        # For aggregate ViewDTOs, validate the referenced domain is in the aggregate
        if is_aggregate:
            if ref_domain_cls not in allowed_domain_classes:
                allowed_names = ", ".join(sorted(c.__name__ for c in allowed_domain_classes))
                agg_hint = (
                    f"\n\n  Hint: '{ref_domain_cls.__name__}' is not a field in '{domain_cls.__name__}'. "
                    f"Declare it as a field in the Aggregate:\n"
                    f"    class {domain_cls.__name__}(Aggregate):\n"
                    f"        {ref_domain_cls.__name__.lower()}: {ref_domain_cls.__name__}"
                )
                raise TypeError(
                    f"In '{cls.__name__}', field '{view_field}' references "
                    f"'{ref_domain_cls.__name__}' which is not in '{domain_cls.__name__}'. "
                    f"Allowed domains: {allowed_names}.{agg_hint}"
                )
        else:
            if ref_domain_cls != domain_cls:
                raise TypeError(
                    f"In '{cls.__name__}', field '{view_field}' references "
                    f"'{ref_domain_cls.__name__}.{domain_field}', but '{cls.__name__}' "
                    f"is bound to '{domain_cls.__name__}'.\n\n"
                    f"  Hint: If you need fields from multiple domains, use an Aggregate:\n"
                    f"    class MyAggregate(Aggregate):\n"
                    f"        {domain_cls.__name__.lower()}: {domain_cls.__name__}\n"
                    f"        {ref_domain_cls.__name__.lower()}: {ref_domain_cls.__name__}\n"
                    f"    class {cls.__name__}(ViewDTO[MyAggregate]): ..."
                )

        # Validate field exists — walk the full path
        target_cls = ref_domain_cls
        if namespace and is_aggregate:
            target_cls = aggregate_domain_fields.get(namespace, ref_domain_cls)

        current_cls = target_cls
        for i, step in enumerate(path):
            if not hasattr(current_cls, "model_fields"):
                break  # can't validate further (e.g. built-in types)
            if step not in current_cls.model_fields:
                traversed = ".".join(path[:i]) if i > 0 else current_cls.__name__
                raise TypeError(
                    f"In '{cls.__name__}', field '{view_field}' has invalid path: "
                    f"'{step}' does not exist on '{current_cls.__name__}' "
                    f"(at '{traversed}.{step}').\n\n"
                    f"  Available fields: {list(current_cls.model_fields.keys())}"
                )
            # Resolve the type of this step to continue validation
            try:
                from typing import Annotated
                step_type = get_type_hints(current_cls).get(step)
                if step_type:
                    origin = get_origin(step_type)
                    if origin is Annotated:
                        step_type = get_args(step_type)[0]
                    if isinstance(step_type, type) and hasattr(step_type, "model_fields"):
                        current_cls = step_type
                    else:
                        break  # leaf field, stop validation
            except Exception:
                break


def _validate_no_private_fields(cls: type, domain_cls: type) -> None:
    """Validate that the ViewDTO doesn't expose Private[T] fields from the domain."""
    try:
        domain_hints = get_type_hints(domain_cls, include_extras=True)
    except Exception:
        return

    view_fields = set(cls.model_fields.keys()) if hasattr(cls, "model_fields") else set()

    for field_name, field_type in domain_hints.items():
        if field_name in view_fields and _is_private_field(field_type):
            raise TypeError(
                f"In '{cls.__name__}', field '{field_name}' is marked as Private in "
                f"'{domain_cls.__name__}' and cannot be exposed in a ViewDTO.\n\n"
                f"  Hint: Remove '{field_name}' from '{cls.__name__}' or use "
                f"'exclude=[{domain_cls.__name__}.{field_name}]' to exclude it."
            )


def _validate_context(cls: type, context: Any) -> None:
    """Validate context against the ViewDTO's context type requirements."""
    context_type = getattr(cls, "__context_type__", None)
    context_required = getattr(cls, "__context_required__", False)

    if context_required and context is None:
        raise TypeError(
            f"'{cls.__name__}' requires context of type "
            f"'{context_type.__name__ if context_type else 'unknown'}'. "
            f"Pass context=... to from_domain()."
        )

    if context_type and context is not None:
        if not isinstance(context, context_type):
            raise TypeError(
                f"Expected context of type '{context_type.__name__}', "
                f"got '{type(context).__name__}'"
            )


def _apply_transform(field_def: Field, value: Any, context: Any) -> Any:
    """Apply a field transform, passing context if the transform accepts it."""
    if field_def._transform_wants_context:
        return field_def.transform(value, context)
    return field_def.transform(value)


class ViewDTO(BaseModel, Generic[D, C], metaclass=ViewDTOMeta):
    """
    Base class for Domain-derived DTOs (outbound data flow).

    Supports single domains and aggregates:
        class UserView(ViewDTO[User]):
            id: int
            username: str

        class OrderView(ViewDTO[Order]):
            amount: int
            customer_name: str = Field(source=Order.customer.username)

    Context support:
        class UserView(ViewDTO[User, Permissions]):       # context required
            ...
        class UserView(ViewDTO[User, Permissions | None]): # context optional
            ...
    """

    __field_mappings__: ClassVar[dict[str, tuple[type, str, str | None, list[str]]]] = {}
    __domain_cls__: ClassVar[type | None] = None
    __context_type__: ClassVar[type | None] = None
    __context_required__: ClassVar[bool] = False
    __is_aggregate_view__: ClassVar[bool] = False
    __hidden_fields__: set[str]

    model_config = ConfigDict(
        extra="ignore",
        coerce_numbers_to_str=True,
        populate_by_name=True,
        validate_by_alias=True,
        validate_by_name=True,
        frozen=True,
        from_attributes=True,
    )

    def __init_subclass__(cls, **kwargs: Any) -> None:
        # Remove our custom kwargs before passing to Pydantic
        kwargs.pop("exclude", None)
        super().__init_subclass__(**kwargs)

    @classmethod
    def __class_getitem__(cls, item: Any) -> Any:
        """Support ViewDTO[Domain] and ViewDTO[Domain, Context]."""
        if not isinstance(item, tuple):
            item = (item,)

        class _GenericViewDTO(cls):  # type: ignore
            __potato_generic_args__ = item

        _GenericViewDTO.__name__ = f"ViewDTO[{', '.join(str(x) for x in item)}]"
        return _GenericViewDTO

    @classmethod
    def from_domain(cls: type[Self], entity: Any, *, context: Any = None) -> Self:
        """
        Build a ViewDTO from a domain/aggregate instance.

        Args:
            entity: The domain or aggregate instance.
            context: Optional context for visibility and computed fields.

        Returns:
            An instance of this ViewDTO.
        """
        _validate_context(cls, context)

        # Execute before_build hooks
        extra_data = {}
        for hook in getattr(cls, "__before_build_hooks__", []):
            func = hook.__func__ if isinstance(hook, classmethod) else hook
            sig = inspect.signature(func)
            hook_kwargs = _build_hook_kwargs(sig, entity, context)

            result = func(cls, **hook_kwargs) if isinstance(hook, classmethod) else func(cls, **hook_kwargs)
            if isinstance(result, dict):
                extra_data.update(result)

        # Extract mapped data
        mapped_data = cls._extract_mapped_data(entity, context)
        mapped_data.update(extra_data)

        # Compute hidden fields for serialization filtering
        hidden_fields = cls._compute_hidden_fields(context)

        # Create instance with ALL fields populated (visibility is serialization-only)
        instance = cls(**mapped_data)

        # Store hidden fields for serialization filtering
        object.__setattr__(instance, "__hidden_fields__", hidden_fields)

        # Handle computed fields (post-init injection)
        cls._inject_computed_fields(instance, entity, context)

        # Execute after_build hooks
        for hook in getattr(cls, "__after_build_hooks__", []):
            sig = inspect.signature(hook)
            hook_kwargs = _build_hook_kwargs(sig, entity, context)
            # Remove 'self' from kwargs — it's passed positionally
            hook_kwargs.pop("self", None)
            hook(instance, **hook_kwargs)

        return instance

    @classmethod
    def from_domains(cls: type[Self], entities: Any, *, context: Any = None) -> list[Self]:
        """
        Build a list of ViewDTOs from domain/aggregate instances.

        Args:
            entities: Iterable of domain or aggregate instances.
            context: Optional context for visibility and computed fields.

        Returns:
            A list of ViewDTO instances.
        """
        return [cls.from_domain(e, context=context) for e in entities]

    @classmethod
    async def afrom_domain(cls: type[Self], entity: Any, *, context: Any = None) -> Self:
        """
        Async version of from_domain(). Awaits async hooks, transforms, and computed fields.

        Args:
            entity: The domain or aggregate instance.
            context: Optional context for visibility and computed fields.

        Returns:
            An instance of this ViewDTO.
        """
        _validate_context(cls, context)

        # Execute before_build hooks (await if async)
        extra_data = {}
        for hook in getattr(cls, "__before_build_hooks__", []):
            func = hook.__func__ if isinstance(hook, classmethod) else hook
            sig = inspect.signature(func)
            hook_kwargs = _build_hook_kwargs(sig, entity, context)

            result = func(cls, **hook_kwargs) if isinstance(hook, classmethod) else func(cls, **hook_kwargs)
            if inspect.isawaitable(result):
                result = await result
            if isinstance(result, dict):
                extra_data.update(result)

        # Extract mapped data (async-aware)
        mapped_data = await cls._aextract_mapped_data(entity, context)
        mapped_data.update(extra_data)

        # Compute hidden fields for serialization filtering
        hidden_fields = cls._compute_hidden_fields(context)

        # Create instance
        instance = cls(**mapped_data)

        # Store hidden fields
        object.__setattr__(instance, "__hidden_fields__", hidden_fields)

        # Handle computed fields (async-aware)
        await cls._ainject_computed_fields(instance, entity, context)

        # Execute after_build hooks (await if async)
        for hook in getattr(cls, "__after_build_hooks__", []):
            sig = inspect.signature(hook)
            hook_kwargs = _build_hook_kwargs(sig, entity, context)
            hook_kwargs.pop("self", None)
            result = hook(instance, **hook_kwargs)
            if inspect.isawaitable(result):
                await result

        return instance

    @classmethod
    async def afrom_domains(cls: type[Self], entities: Any, *, context: Any = None) -> list[Self]:
        """
        Async version of from_domains(). Processes entities concurrently with asyncio.gather().

        Args:
            entities: Iterable of domain or aggregate instances.
            context: Optional context for visibility and computed fields.

        Returns:
            A list of ViewDTO instances.
        """
        return list(await asyncio.gather(
            *(cls.afrom_domain(e, context=context) for e in entities)
        ))

    @classmethod
    def _compute_hidden_fields(cls, context: Any) -> set[str]:
        """Compute which fields should be hidden based on visibility predicates."""
        hidden: set[str] = set()
        potato_fields = getattr(cls, "__potato_fields__", {})
        for field_name, field_def in potato_fields.items():
            if field_def.visible is not None:
                if context is None or not field_def.visible(context):
                    hidden.add(field_name)
        return hidden

    @classmethod
    def _extract_mapped_data(
        cls: type[Self],
        entity: Any,
        context: Any = None,
    ) -> dict[str, Any]:
        """Extract all field values from the entity."""
        mapped_data: dict[str, Any] = {}
        field_mappings = getattr(cls, "__field_mappings__", {})
        potato_fields = getattr(cls, "__potato_fields__", {})
        is_aggregate = getattr(cls, "__is_aggregate_view__", False)

        # 1. Explicitly mapped fields (Field(source=...))
        for view_field, (domain_cls, domain_field, namespace, path) in field_mappings.items():
            value = _resolve_field_value(entity, namespace, path, is_aggregate)
            if value is not _SENTINEL:
                # Apply transform if present
                field_def = potato_fields.get(view_field)
                if field_def and field_def.transform:
                    value = _apply_transform(field_def, value, context)
                # Check if value should be auto-built as nested ViewDTO
                value = _maybe_build_nested_viewdto(cls, view_field, value, context)
                mapped_data[view_field] = value

        # 2. Auto-mapped fields (match by name)
        for field_name in cls.model_fields:
            if field_name in mapped_data:
                continue

            value = _SENTINEL

            if is_aggregate:
                # For aggregates: auto-map from aggregate-level attributes
                if hasattr(entity, field_name):
                    value = getattr(entity, field_name)
            else:
                # For single-domain: auto-map by matching field name
                if hasattr(entity, field_name):
                    value = getattr(entity, field_name)

            if value is not _SENTINEL:
                value = _maybe_build_nested_viewdto(cls, field_name, value, context)
                mapped_data[field_name] = value

        return mapped_data

    @classmethod
    async def _aextract_mapped_data(
        cls: type[Self],
        entity: Any,
        context: Any = None,
    ) -> dict[str, Any]:
        """Async version of _extract_mapped_data. Awaits async transforms."""
        mapped_data: dict[str, Any] = {}
        field_mappings = getattr(cls, "__field_mappings__", {})
        potato_fields = getattr(cls, "__potato_fields__", {})
        is_aggregate = getattr(cls, "__is_aggregate_view__", False)

        # 1. Explicitly mapped fields (Field(source=...))
        for view_field, (domain_cls, domain_field, namespace, path) in field_mappings.items():
            value = _resolve_field_value(entity, namespace, path, is_aggregate)
            if value is not _SENTINEL:
                field_def = potato_fields.get(view_field)
                if field_def and field_def.transform:
                    value = _apply_transform(field_def, value, context)
                    if inspect.isawaitable(value):
                        value = await value
                value = await _amaybe_build_nested_viewdto(cls, view_field, value, context)
                mapped_data[view_field] = value

        # 2. Auto-mapped fields (match by name)
        for field_name in cls.model_fields:
            if field_name in mapped_data:
                continue

            value = _SENTINEL
            if is_aggregate:
                if hasattr(entity, field_name):
                    value = getattr(entity, field_name)
            else:
                if hasattr(entity, field_name):
                    value = getattr(entity, field_name)

            if value is not _SENTINEL:
                value = await _amaybe_build_nested_viewdto(cls, field_name, value, context)
                mapped_data[field_name] = value

        return mapped_data

    @classmethod
    def _inject_computed_fields(
        cls, instance: Self, entity: Any, context: Any
    ) -> None:
        """Execute @computed methods and set their values on the instance."""
        computed_methods = getattr(cls, "__computed_methods__", {})

        for name, member in computed_methods.items():
            sig = inspect.signature(member)
            kwargs: dict[str, Any] = {}

            for param_name, param in sig.parameters.items():
                if param_name == "self":
                    continue
                if param_name == "context":
                    kwargs["context"] = context
                elif param.annotation != inspect.Parameter.empty:
                    # Match by type annotation
                    if isinstance(entity, param.annotation):
                        kwargs[param_name] = entity
                    # For aggregates, check sub-entities
                    elif hasattr(entity, "__aggregate_domain_fields__"):
                        for field_name, domain_type in entity.__aggregate_domain_fields__.items():
                            sub_entity = getattr(entity, field_name, None)
                            if sub_entity is not None and isinstance(sub_entity, param.annotation):
                                kwargs[param_name] = sub_entity
                                break
                else:
                    kwargs[param_name] = entity

            val = member(instance, **kwargs)
            object.__setattr__(instance, name, val)

    @classmethod
    async def _ainject_computed_fields(
        cls, instance: Self, entity: Any, context: Any
    ) -> None:
        """Async version of _inject_computed_fields. Awaits async computed methods."""
        computed_methods = getattr(cls, "__computed_methods__", {})

        for name, member in computed_methods.items():
            sig = inspect.signature(member)
            kwargs: dict[str, Any] = {}

            for param_name, param in sig.parameters.items():
                if param_name == "self":
                    continue
                if param_name == "context":
                    kwargs["context"] = context
                elif param.annotation != inspect.Parameter.empty:
                    if isinstance(entity, param.annotation):
                        kwargs[param_name] = entity
                    elif hasattr(entity, "__aggregate_domain_fields__"):
                        for field_name, domain_type in entity.__aggregate_domain_fields__.items():
                            sub_entity = getattr(entity, field_name, None)
                            if sub_entity is not None and isinstance(sub_entity, param.annotation):
                                kwargs[param_name] = sub_entity
                                break
                else:
                    kwargs[param_name] = entity

            val = member(instance, **kwargs)
            if inspect.isawaitable(val):
                val = await val
            object.__setattr__(instance, name, val)

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        """Override to include computed fields and exclude hidden fields."""
        result = super().model_dump(**kwargs)

        # Include computed fields (set as attributes, not in model_fields)
        computed_methods = getattr(self.__class__, "__computed_methods__", {})
        if computed_methods:
            exclude = kwargs.get("exclude") or set()
            exclude_none = kwargs.get("exclude_none", False)
            mode = kwargs.get("mode", "python")
            for name in computed_methods:
                if name in exclude:
                    continue
                val = getattr(self, name, None)
                if exclude_none and val is None:
                    continue
                if mode == "json" and hasattr(val, "isoformat"):
                    val = val.isoformat()
                result[name] = val

        # Exclude hidden fields
        hidden = getattr(self, "__hidden_fields__", set())
        if hidden:
            for field_name in hidden:
                result.pop(field_name, None)
        return result

    def model_dump_json(self, **kwargs: Any) -> str:
        """Override to include computed fields and exclude hidden fields."""
        import json

        indent = kwargs.pop("indent", None)
        data = self.model_dump(mode="json", **kwargs)
        return json.dumps(data, indent=indent)


# Sentinel for missing values
_SENTINEL = object()


def _resolve_field_value(
    entity: Any,
    namespace: str | None,
    path: list[str],
    is_aggregate: bool,
) -> Any:
    """Resolve a field value from an entity, following namespace and path."""
    target = entity

    # If there's a namespace (aggregate field name), navigate to that sub-entity first
    if namespace and is_aggregate:
        target = getattr(entity, namespace, _SENTINEL)
        if target is _SENTINEL:
            return _SENTINEL

    # Follow the path
    current = target
    for step in path:
        if hasattr(current, step):
            current = getattr(current, step)
        else:
            return _SENTINEL

    return current


def _maybe_build_nested_viewdto(
    parent_cls: type,
    field_name: str,
    value: Any,
    context: Any,
) -> Any:
    """If the field's type is a ViewDTO subclass, auto-build it."""
    if value is None:
        return value

    try:
        hints = get_type_hints(parent_cls)
    except Exception:
        return value

    field_type = hints.get(field_name)
    if field_type is None:
        return value

    # Check for list[ViewDTO]
    is_list, inner_type = _unwrap_list_type(field_type)
    if is_list and _is_viewdto_type(inner_type):
        if isinstance(value, (list, tuple)):
            return [inner_type.from_domain(item, context=context) for item in value]
        return value

    # Check for single ViewDTO
    if _is_viewdto_type(field_type):
        return field_type.from_domain(value, context=context)

    return value


async def _amaybe_build_nested_viewdto(
    parent_cls: type,
    field_name: str,
    value: Any,
    context: Any,
) -> Any:
    """Async version: If the field's type is a ViewDTO subclass, auto-build it using afrom_domain."""
    if value is None:
        return value

    try:
        hints = get_type_hints(parent_cls)
    except Exception:
        return value

    field_type = hints.get(field_name)
    if field_type is None:
        return value

    # Check for list[ViewDTO]
    is_list, inner_type = _unwrap_list_type(field_type)
    if is_list and _is_viewdto_type(inner_type):
        if isinstance(value, (list, tuple)):
            return list(await asyncio.gather(
                *(inner_type.afrom_domain(item, context=context) for item in value)
            ))
        return value

    # Check for single ViewDTO
    if _is_viewdto_type(field_type):
        return await field_type.afrom_domain(value, context=context)

    return value
