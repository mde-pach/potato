from typing import TYPE_CHECKING, dataclass_transform

from pydantic import BaseModel
from pydantic._internal._model_construction import (
    ModelMetaclass,
    NoInitField,
    PydanticModelField,
    PydanticModelPrivateAttr,
)


class FieldProxy:
    """Proxy to reference a field from a model."""

    def __init__(self, model_cls: type, field_name: str):
        self.model_cls = model_cls
        self.field_name = field_name

    def __repr__(self):
        return f"FieldProxy({self.model_cls.__name__}.{self.field_name})"


@dataclass_transform(
    kw_only_default=True,
    field_specifiers=(PydanticModelField, NoInitField, PydanticModelPrivateAttr),
)
class DomainMeta(ModelMetaclass):
    """Metaclass that makes fields accessible as class attributes."""

    if not TYPE_CHECKING:

        def __getattr__(cls, name: str):
            if cls.__name__ == "Domain":
                return super().__getattr__(name)

            annotations = getattr(cls, "__annotations__", {})

            if name in annotations:
                return FieldProxy(cls, name)

            return super().__getattr__(name)


class Domain(BaseModel, metaclass=DomainMeta):
    pass
