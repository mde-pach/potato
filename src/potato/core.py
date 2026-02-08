from typing import Annotated, Any, Callable, TypeVar, TYPE_CHECKING, TypeAlias

T = TypeVar("T")


class _Unassigned:
    """Sentinel for Auto fields not yet assigned by infrastructure."""
    _msg = (
        "This Auto field has not been assigned a value yet. "
        "Auto fields are populated by the infrastructure layer (e.g. database autoincrement)."
    )
    def __repr__(self) -> str:
        return "<Unassigned>"
    def __str__(self) -> str:
        raise AttributeError(self._msg)
    def __int__(self) -> int:
        raise AttributeError(self._msg)
    def __float__(self) -> float:
        raise AttributeError(self._msg)
    def __bool__(self) -> bool:
        # Return False instead of raising: older Pydantic's smart_deepcopy
        # calls `not obj` on field defaults during model construction.
        return False
    def __eq__(self, other: object) -> bool:
        if isinstance(other, _Unassigned):
            return True
        raise AttributeError(self._msg)
    def __hash__(self) -> int:
        raise AttributeError(self._msg)
    def __lt__(self, other: object) -> bool:
        raise AttributeError(self._msg)
    def __le__(self, other: object) -> bool:
        raise AttributeError(self._msg)
    def __gt__(self, other: object) -> bool:
        raise AttributeError(self._msg)
    def __ge__(self, other: object) -> bool:
        raise AttributeError(self._msg)

UNASSIGNED = _Unassigned()


class AutoMarker:
    """Marker for auto-generated/managed fields (id, timestamps, etc.)."""
    pass


Auto: TypeAlias = Annotated[T, AutoMarker]


class PrivateMarker:
    """Marker for private fields that should never be exposed in any DTO."""
    pass


Private: TypeAlias = Annotated[T, PrivateMarker]


if TYPE_CHECKING:
    def Field(
        source: Any = None,
        compute: Callable[..., Any] | None = None,
        transform: Callable[[Any], Any] | None = None,
        visible: Callable[[Any], bool] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Configuration for Potato fields."""
        return None
else:
    class Field:
        """
        Configuration for Potato fields.

        Usage:
            # Map from a source field
            name: str = Field(source=User.username)

            # With transformation (1-arg or 2-arg with context)
            created_at: str = Field(source=User.created_at, transform=lambda dt: dt.isoformat())
            email: str = Field(source=User.email, transform=lambda val, ctx: val if ctx.is_admin else "***")

            # With visibility control
            email: str = Field(visible=lambda ctx: ctx.is_admin)

        Args:
            source: The source field to map from (e.g., User.username).
            compute: A callable to compute the value.
            transform: A callable to transform the raw value after extraction.
                       Can be 1-arg (value) or 2-arg (value, context).
            visible: A callable that receives context and returns whether the field is visible.
            **kwargs: Additional arguments passed to Pydantic's FieldInfo.
        """
        def __init__(
            self,
            source: Any = None,
            compute: Callable[..., Any] | None = None,
            transform: Callable[[Any], Any] | None = None,
            visible: Callable[[Any], bool] | None = None,
            **kwargs: Any,
        ):
            self.source = source
            self.compute = compute
            self.transform = transform
            self.visible = visible
            self.pydantic_kwargs = kwargs
            self._transform_wants_context: bool = False


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


def before_build(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator for a classmethod called before ViewDTO construction.

    The method receives the entity and context, and returns a dict of extra data to merge.
    Automatically wraps the function as a classmethod.

    Usage:
        @before_build
        def enrich(cls, entity: Order, context: AuditCtx) -> dict:
            return {"reviewer_name": context.get_reviewer(entity.reviewer_id)}
    """
    # Unwrap if user already applied @classmethod
    raw = func.__func__ if isinstance(func, classmethod) else func
    raw._is_before_build = True  # type: ignore
    return classmethod(raw)


def after_build(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator for an instance method called after ViewDTO construction.

    Can validate, log, or perform side effects.

    Usage:
        @after_build
        def validate(self) -> None:
            if not self.reviewer_name:
                raise ValueError("Reviewer required for audit views")
    """
    func._is_after_build = True  # type: ignore
    return func
