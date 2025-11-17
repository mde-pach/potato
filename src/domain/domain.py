from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    ClassVar,
    Self,
    TypeVarTuple,
    dataclass_transform,
    get_args,
    get_origin,
    get_type_hints,
)

from pydantic import BaseModel
from pydantic._internal._model_construction import (
    ModelMetaclass,
    NoInitField,
    PydanticModelField,
    PydanticModelPrivateAttr,
)

from .aggregates import Aggregate


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
    """Metaclass that makes fields accessible as class attributes and handles Aggregate."""

    def __new__(
        mcs: type,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        **kwargs: Any,
    ) -> type:
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)  # type: ignore

        # Check if any base class has Pydantic generic metadata with Aggregate
        for base in cls.__bases__:
            if hasattr(base, "__pydantic_generic_metadata__"):
                metadata = base.__pydantic_generic_metadata__
                # metadata['args'] contains the type arguments passed to the generic
                if "args" in metadata and metadata["args"]:
                    # Check if the first argument is Aggregate[...]
                    first_arg = metadata["args"][0]
                    aggregate_origin = get_origin(first_arg)
                    if aggregate_origin is not None:
                        # Get the domain types from Aggregate[User, Price, ...]
                        aggregate_args = get_args(first_arg)
                        if aggregate_args:
                            # Store metadata for the static build method
                            cls.__aggregate_domain_types__ = aggregate_args  # type: ignore
                            # Extract field mappings
                            DomainMeta._extract_field_mappings(cls)
                            break

        return cls

    @staticmethod
    def _extract_field_mappings(cls: type) -> None:
        """Extract field mappings from Annotated types with FieldProxy metadata."""

        field_mappings: dict[str, tuple[type, str]] = {}
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
                            # Map field to (domain_class, domain_field_name)
                            field_mappings[field_name] = (
                                metadata.model_cls,
                                metadata.field_name,
                            )
                            break
        except Exception:
            # If we can't get type hints, just skip
            pass

        # Store field mappings on the class for use by build method
        cls.__aggregate_field_mappings__ = field_mappings  # type: ignore

    if not TYPE_CHECKING:

        def __getattr__(cls, name: str):
            if cls.__name__ == "Domain":
                return super().__getattr__(name)

            annotations = getattr(cls, "__annotations__", {})

            if name in annotations:
                return FieldProxy(cls, name)

            return super().__getattr__(name)


D = TypeVarTuple("D")
A = Aggregate[*D]


class Domain[T: A | None = None](BaseModel, metaclass=DomainMeta):
    __aggregate_domain_types__: ClassVar[tuple[type, ...]] = ()
    __aggregate_field_mappings__: ClassVar[dict[str, tuple[type, str]]] = {}

    @classmethod
    def build(cls: type[Self], *domains: Any) -> Self:
        """Build an aggregate instance from domain instances.

        For aggregates defined as Domain[Aggregate[Type1, Type2, ...]],
        this method automatically maps fields from the provided domain instances.
        """
        # Check if this is an aggregate
        if (
            not hasattr(cls, "__aggregate_domain_types__")
            or not cls.__aggregate_domain_types__
        ):
            raise NotImplementedError(
                f"{cls.__name__} is not an aggregate. "
                "Define it as Domain[Aggregate[Type1, Type2, ...]] to use build()."
            )

        expected_types = cls.__aggregate_domain_types__
        mappings = getattr(cls, "__aggregate_field_mappings__", {})

        # Verify we have the right number of domains
        if len(domains) != len(expected_types):
            raise ValueError(
                f"Expected {len(expected_types)} domain instances, got {len(domains)}"
            )

        # Create a mapping from domain type to domain instance
        domain_instances = {}
        for domain_type, domain_instance in zip(expected_types, domains):
            domain_instances[domain_type] = domain_instance

        # Build the aggregate data
        aggregate_data = {}

        # Map fields according to field_mappings
        for field_name, (domain_cls, domain_field) in mappings.items():
            if domain_cls in domain_instances:
                domain_instance = domain_instances[domain_cls]
                domain_data = domain_instance.model_dump()
                if domain_field in domain_data:
                    aggregate_data[field_name] = domain_data[domain_field]

        # Add any domain instances directly (for fields that hold full domain objects)
        for field_name in cls.model_fields:
            if field_name not in aggregate_data:
                # Check if this field's type matches one of our domain types
                for domain_type, domain_instance in domain_instances.items():
                    field_info = cls.model_fields[field_name]
                    # Try to match the field annotation to a domain type
                    if hasattr(field_info, "annotation"):
                        if field_info.annotation == domain_type:
                            aggregate_data[field_name] = domain_instance
                            break

        return cls(**aggregate_data)
