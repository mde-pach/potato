from typing import Any, Generic

from pydantic import BaseModel

from .base import DTOMeta, D

class BuildDTO(BaseModel, Generic[D], metaclass=DTOMeta):
    """
    Base class for constructing Domain models from external data (inbound data flow).
    """
    _domain_cls: type[D]

    @classmethod
    def __class_getitem__(cls, item: Any) -> Any:
        """
        Support BuildDTO[Domain].
        """
        if not isinstance(item, tuple):
            item = (item,)
        
        class _GenericBuildDTO(cls): # type: ignore
            __potato_generic_args__ = item
            
        _GenericBuildDTO.__name__ = f"BuildDTO[{', '.join(str(x) for x in item)}]"
        return _GenericBuildDTO

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        super().__pydantic_init_subclass__(**kwargs)
        
        # Extract the Domain type D
        domain_cls = None
        # Check Potato generic args
        if hasattr(cls, "__potato_generic_args__"):
            args = cls.__potato_generic_args__
            if args:
                domain_cls = args[0]
        
        if domain_cls:
            cls._domain_cls = domain_cls

    def to_domain(self, **kwargs: Any) -> D:
        """
        Convert the DTO to a Domain instance.
        
        Args:
            **kwargs: Additional fields required by the Domain (e.g., System fields like id)
            
        Returns:
            An instance of the Domain class D
        """
        if not hasattr(self, "_domain_cls") or not self._domain_cls:
            raise ValueError("BuildDTO must have a Domain type argument (e.g. BuildDTO[User])")
            
        # Combine DTO data with kwargs
        data = self.model_dump()
        data.update(kwargs)
        
        return self._domain_cls(**data)
