from typing import Annotated, Any, Generic, get_args, get_origin

from pydantic import BaseModel

from potato.core import AutoMarker, PrivateMarker

from .base import D, BuildDTOMeta


def _is_auto_or_private(field_type: Any) -> bool:
    """Check if a type is Auto[T] or Private[T]."""
    if get_origin(field_type) is Annotated:
        for meta in get_args(field_type)[1:]:
            if isinstance(meta, (AutoMarker, PrivateMarker)) or meta in (AutoMarker, PrivateMarker):
                return True
    return False


class BuildDTO(BaseModel, Generic[D], metaclass=BuildDTOMeta):
    """
    Base class for constructing Domain models from external data (inbound data flow).

    Supports partial updates via partial=True:
        class UserUpdate(BuildDTO[User], partial=True):
            username: str
            email: str
            # All fields become Optional with default None

    Supports field mapping via Field(source=...):
        class UserCreate(BuildDTO[User]):
            login: str = Field(source=User.username)
            # "login" in DTO → "username" in domain
    """
    _domain_cls: type[D]

    @classmethod
    def __class_getitem__(cls, item: Any) -> Any:
        """Support BuildDTO[Domain]."""
        if not isinstance(item, tuple):
            item = (item,)

        class _GenericBuildDTO(cls):  # type: ignore
            __potato_generic_args__ = item

        _GenericBuildDTO.__name__ = f"BuildDTO[{', '.join(str(x) for x in item)}]"
        return _GenericBuildDTO

    def __init_subclass__(cls, **kwargs: Any) -> None:
        kwargs.pop("partial", None)
        kwargs.pop("exclude", None)
        super().__init_subclass__(**kwargs)

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        super().__pydantic_init_subclass__(**kwargs)

        # Extract the Domain type D
        domain_cls = None
        for base in cls.__mro__:
            if hasattr(base, "__potato_generic_args__"):
                args = base.__potato_generic_args__
                if args:
                    domain_cls = args[0]
                    break

        if domain_cls:
            cls._domain_cls = domain_cls

    def _remap_to_domain_names(self, data: dict[str, Any]) -> dict[str, Any]:
        """Remap DTO field names to domain field names using __build_field_mappings__."""
        mappings = getattr(self.__class__, "__build_field_mappings__", {})
        if not mappings:
            return data

        remapped: dict[str, Any] = {}
        for key, value in data.items():
            domain_key = mappings.get(key, key)
            remapped[domain_key] = value
        return remapped

    def to_domain(self, **kwargs: Any) -> D:
        """
        Convert the DTO to a Domain instance.

        Auto and Private fields from the domain are excluded from the DTO.
        Extra fields on the DTO that don't exist on the domain are filtered out.
        Field mappings (Field(source=...)) are applied to remap DTO names to domain names.
        Pass additional domain fields via **kwargs if needed.

        Args:
            **kwargs: Additional fields required by the Domain (e.g., Auto fields like id)

        Returns:
            An instance of the Domain class D
        """
        if not hasattr(self, "_domain_cls") or not self._domain_cls:
            raise ValueError("BuildDTO must have a Domain type argument (e.g. BuildDTO[User])")

        data = self.model_dump()

        # Remap DTO field names → domain field names
        data = self._remap_to_domain_names(data)

        # Filter to only fields that exist on the domain
        domain_field_names = set(self._domain_cls.model_fields.keys())
        domain_data = {k: v for k, v in data.items() if k in domain_field_names}

        # kwargs override everything
        domain_data.update(kwargs)

        return self._domain_cls(**domain_data)

    def apply_to(self, entity: D) -> D:
        """
        Apply partial updates to an existing domain instance.

        Only fields that were explicitly set (not defaults) are updated.
        Field mappings (Field(source=...)) are applied to remap DTO names to domain names.
        Returns a new domain instance (immutability-friendly).

        Args:
            entity: The existing domain instance to update.

        Returns:
            A new domain instance with updates applied.
        """
        if not hasattr(self, "_domain_cls") or not self._domain_cls:
            raise ValueError("BuildDTO must have a Domain type argument (e.g. BuildDTO[User])")

        update_data = self.model_dump(exclude_unset=True)

        # Remap DTO field names → domain field names
        update_data = self._remap_to_domain_names(update_data)

        entity_data = entity.model_dump()
        entity_data.update(update_data)

        return self._domain_cls(**entity_data)
