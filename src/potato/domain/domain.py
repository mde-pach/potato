"""
Domain module - Core domain model implementation.

Provides the Domain base class for building rich domain models
with class-attribute field access for DTO field mapping.
"""

import copy
from typing import (
    Annotated,
    TYPE_CHECKING,
    Any,
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

from potato.core import AutoMarker, UNASSIGNED
from potato.types import FieldProxy


def _is_auto_field(field_type: Any) -> bool:
    """Check if a type is Auto[T] (has AutoMarker in metadata)."""
    if get_origin(field_type) is Annotated:
        for meta in get_args(field_type)[1:]:
            if isinstance(meta, AutoMarker) or meta is AutoMarker:
                return True
    return False


@dataclass_transform(
    kw_only_default=True,
    field_specifiers=(PydanticModelField, NoInitField, PydanticModelPrivateAttr),
)
class DomainMeta(ModelMetaclass):
    """
    Metaclass for Domain models.

    Provides field access as class attributes:
        User.username → FieldProxy(User, "username")
    """

    def __new__(
        mcs: type,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        **kwargs: Any,
    ) -> type:
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)  # type: ignore

        # Set UNASSIGNED as default for Auto fields
        if name != "Domain":
            try:
                hints = get_type_hints(cls, include_extras=True)
            except Exception:
                hints = {}

            has_auto = False
            for field_name, field_type in hints.items():
                if _is_auto_field(field_type) and field_name in cls.model_fields:
                    field_info = copy.copy(cls.model_fields[field_name])
                    field_info.default = UNASSIGNED
                    cls.model_fields[field_name] = field_info
                    has_auto = True

            if has_auto:
                cls.model_rebuild(force=True)

        return cls

    if not TYPE_CHECKING:

        def __getattr__(cls, name: str):
            """
            Enable field access as class attributes (e.g., User.username → FieldProxy).
            """
            if cls.__name__ == "Domain":
                return super().__getattr__(name)

            annotations = getattr(cls, "__annotations__", {})

            if name in annotations:
                # Don't return FieldProxy when Pydantic is collecting model fields
                import inspect

                frame = inspect.currentframe()
                try:
                    check_frame = frame.f_back
                    for _ in range(5):
                        if check_frame is None:
                            break
                        if "collect_model_fields" in check_frame.f_code.co_name:
                            raise AttributeError(
                                f"type object '{cls.__name__}' has no attribute '{name}'"
                            )
                        check_frame = check_frame.f_back
                finally:
                    del frame

                return FieldProxy(cls, name)

            return super().__getattr__(name)


class Domain(BaseModel, metaclass=DomainMeta):
    """
    Base class for all domain models.

    Usage:
        >>> class User(Domain):
        ...     id: int
        ...     username: str
        ...     email: str

    Field access as class attributes for ViewDTO mapping:
        >>> User.username  # → FieldProxy(User, "username")
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
