from typing import Self, TypeVarTuple, dataclass_transform

from pydantic._internal._model_construction import (
    NoInitField,
    PydanticModelField,
    PydanticModelPrivateAttr,
)

D = TypeVarTuple("D")


# @dataclass_transform(
#     kw_only_default=True,
#     field_specifiers=(PydanticModelField, NoInitField, PydanticModelPrivateAttr),
# )
class Aggregate[*D]:
    @classmethod
    def build(cls: type[Self], *args: *D) -> Self:
        raise NotImplementedError("Subclasses must implement this method")
