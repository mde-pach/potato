from typing import (
    Any,
    TypeVar,
    dataclass_transform,
)

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
