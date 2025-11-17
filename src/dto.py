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

from pydantic import BaseModel, ConfigDict, Field
from pydantic._internal._model_construction import (
    ModelMetaclass,
    NoInitField,
    PydanticModelField,
    PydanticModelPrivateAttr,
)

if TYPE_CHECKING:
    from domain import Domain, FieldProxy
else:
    from domain import FieldProxy


@dataclass_transform(
    kw_only_default=True,
    field_specifiers=(PydanticModelField, NoInitField, PydanticModelPrivateAttr),
)
class DTOMeta(ModelMetaclass):
    def __new__(
        mcs: type,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        **kwargs: Any,
    ) -> type:
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)  # type: ignore
        # import pdb

        # pdb.set_trace()
        # # Extract domain type from generic parameter
        # if hasattr(cls, "__orig_bases__"):
        #     for base in cls.__orig_bases__:
        #         origin = get_origin(base)
        #         if origin is not None:
        #             args = get_args(base)
        #             if args:
        #                 cls.__domain__ = args[0]  # type: ignore
        #                 break
        return cls


class ViewDTOMeta(DTOMeta):
    """Metaclass that automatically extracts and stores the entity type from generics."""

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        **kwargs: Any,
    ) -> type:
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)
        # Extract field mappings from Annotated types with FieldProxy metadata
        field_mappings: dict[str, str] = {}
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
                            # Map view field name to domain field name
                            field_mappings[field_name] = metadata.field_name
                            break
        except Exception:
            # If we can't get type hints, just skip
            pass

        if field_mappings:
            cls.__field_mappings__ = field_mappings  # type: ignore

        return cls


class ViewDTO[D: Domain](BaseModel, metaclass=ViewDTOMeta):
    __field_mappings__: ClassVar[dict[str, str]] = {}

    model_config = ConfigDict(
        extra="allow",
        coerce_numbers_to_str=True,
        populate_by_name=True,
        validate_by_alias=True,
        validate_by_name=True,
        frozen=True,
        from_attributes=True,
    )

    @classmethod
    def build(cls: type[Self], domain: D) -> Self:
        # If we have field mappings, we need to remap the data
        if hasattr(cls, "__field_mappings__") and cls.__field_mappings__:
            domain_data = domain.model_dump()
            mapped_data = {}

            # Map fields according to __field_mappings__
            for view_field, domain_field in cls.__field_mappings__.items():
                if domain_field in domain_data:
                    mapped_data[view_field] = domain_data[domain_field]

            # Add any other fields that weren't explicitly mapped
            for field_name in cls.model_fields:
                if field_name not in mapped_data and field_name in domain_data:
                    mapped_data[field_name] = domain_data[field_name]

            return cls(**mapped_data)
        else:
            return cls(**domain.model_dump())


class BuildDTO[D: Domain](BaseModel, metaclass=DTOMeta):
    @classmethod
    def build(cls: type[Self], domain: D) -> Self:
        return cls(**domain.model_dump())
