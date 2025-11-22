from typing import Annotated, Any, Callable, TypeVar, TYPE_CHECKING

T = TypeVar("T")


class SystemMarker:
    """Marker for system-managed fields."""
    pass


class _SystemAlias:
    """
    Helper to create System[T] types.
    
    Usage:
        id: System[int]
        
    This resolves to Annotated[int, SystemMarker] which Pydantic handles gracefully,
    while allowing Potato to identify system fields.
    """
    def __class_getitem__(cls, item):
        return Annotated[item, SystemMarker]


System = _SystemAlias


if TYPE_CHECKING:
    def Field(
        source: Any = None,
        compute: Callable[..., Any] | None = None,
        system: bool = False,
        **kwargs: Any,
    ) -> Any:
        """
        Configuration for Potato fields.
        """
        return None
else:
    class Field:
        """
        Configuration for Potato fields.
        
        Usage:
            # Map from a source field
            name: str = Field(source=User.username)
            
            # Computed field (lambda)
            full_name: str = Field(compute=lambda u: f"{u.first} {u.last}")
            
        Args:
            source: The source field to map from (e.g., User.username).
            compute: A callable to compute the value.
            system: (Deprecated) Use System[T] instead.
            **kwargs: Additional arguments passed to Pydantic's FieldInfo.
        """
        def __init__(
            self,
            source: Any = None,
            compute: Callable[..., Any] | None = None,
            system: bool = False,
            **kwargs: Any,
        ):
            self.source = source
            self.compute = compute
            self.system = system
            self.pydantic_kwargs = kwargs


def computed(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to mark a method as a computed field.
    
    Usage:
        @computed
        def full_name(self, user: User) -> str:
            return f"{user.first} {user.last}"
            
    The framework will automatically inject 'context' if requested in the signature.
    """
    func._is_computed = True  # type: ignore
    return func
