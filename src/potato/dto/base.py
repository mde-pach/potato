from typing import (
    Any,
    TypeVar,
    dataclass_transform,
)

from pydantic import Field as PydanticField
from pydantic._internal._model_construction import (
    ModelMetaclass,
    NoInitField,
    PydanticModelField,
    PydanticModelPrivateAttr,
)

D = TypeVar("D")
C = TypeVar("C", default=None)


@dataclass_transform(
    kw_only_default=True,
    field_specifiers=(PydanticModelField, NoInitField, PydanticModelPrivateAttr),
)
class DTOMeta(ModelMetaclass):
    """
    Base metaclass for DTO classes.

    Handles partial=True and exclude= parameters.
    """

    def __new__(
        mcs: type,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        **kwargs: Any,
    ) -> type:
        partial = kwargs.pop("partial", False)
        exclude = kwargs.pop("exclude", None)

        cls = super().__new__(mcs, name, bases, namespace, **kwargs)  # type: ignore

        if name not in ("BuildDTO", "ViewDTO"):
            if exclude is not None:
                _apply_exclude_to_build_model(cls, exclude)

            if partial:
                cls.__potato_partial__ = True  # type: ignore
                _apply_partial_to_model(cls)

        return cls


class BuildDTOMeta(DTOMeta):
    """
    Metaclass for BuildDTO that handles Field(source=...) mapping.

    Extracts reverse field mappings (dto_name -> domain_name) at class definition time.
    """

    def __new__(
        mcs: type,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        **kwargs: Any,
    ) -> type:
        from potato.core import Field
        from potato.types import FieldProxy

        # Pre-process namespace to handle Potato Field objects
        potato_fields: dict[str, Field] = {}
        for k, v in list(namespace.items()):
            if isinstance(v, Field):
                potato_fields[k] = v
                if v.pydantic_kwargs:
                    namespace[k] = PydanticField(**v.pydantic_kwargs)
                else:
                    namespace[k] = PydanticField()

        cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        if potato_fields:
            cls.__potato_fields__ = potato_fields  # type: ignore

        # Build reverse field mappings: {dto_field_name: domain_field_name}
        if name != "BuildDTO" and potato_fields:
            build_mappings: dict[str, str] = {}
            for field_name, field_def in potato_fields.items():
                if field_def.source and isinstance(field_def.source, FieldProxy):
                    proxy = field_def.source
                    if len(proxy.path) > 1:
                        raise TypeError(
                            f"In '{name}', field '{field_name}' uses a deep path "
                            f"'{'.'.join(proxy.path)}'. BuildDTO only supports "
                            f"flat field references (e.g., Field(source=Domain.field))."
                        )
                    build_mappings[field_name] = proxy.field_name

            if build_mappings:
                cls.__build_field_mappings__ = build_mappings  # type: ignore

            # Validate mappings against domain class
            _validate_build_field_mappings(cls, build_mappings)

        return cls


def _validate_build_field_mappings(cls: type, mappings: dict[str, str]) -> None:
    """Validate that BuildDTO field mappings reference existing domain fields."""
    # Find domain class
    domain_cls = None
    for base in cls.__mro__:
        if hasattr(base, "__potato_generic_args__"):
            args = base.__potato_generic_args__
            if args:
                domain_cls = args[0]
                break

    if not domain_cls or not mappings:
        return

    domain_fields = set(domain_cls.model_fields.keys()) if hasattr(domain_cls, "model_fields") else set()
    if not domain_fields:
        return

    for dto_field, domain_field in mappings.items():
        if domain_field not in domain_fields:
            raise TypeError(
                f"In '{cls.__name__}', field '{dto_field}' maps to "
                f"'{domain_field}' which does not exist on "
                f"'{domain_cls.__name__}'.\n\n"
                f"  Available fields: {sorted(domain_fields)}"
            )


def _apply_exclude_to_build_model(cls: type, exclude: list) -> None:
    """Remove excluded fields from the model, then rebuild."""
    from potato.types import FieldProxy

    excluded_names: set[str] = set()
    for item in exclude:
        if isinstance(item, FieldProxy):
            excluded_names.add(item.field_name)
        elif isinstance(item, str):
            excluded_names.add(item)

    changed = False
    for field_name in list(cls.model_fields.keys()):
        if field_name in excluded_names:
            del cls.model_fields[field_name]
            changed = True

    if changed:
        cls.model_rebuild(force=True)


def _apply_partial_to_model(cls: type) -> None:
    """Make all model fields Optional with default None, then rebuild."""
    import copy

    for field_name, field_info in list(cls.model_fields.items()):
        # Make the field optional with default None
        new_info = copy.copy(field_info)
        new_info.default = None
        new_info.annotation = field_info.annotation | None
        cls.model_fields[field_name] = new_info

    # Rebuild the model to pick up the changes
    cls.model_rebuild(force=True)
