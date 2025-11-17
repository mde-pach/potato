from typing import TYPE_CHECKING, Any, get_args, get_origin

if TYPE_CHECKING:
    # For type checkers, use the standard Annotated
    from typing import Annotated
else:
    # At runtime, use our custom Annotated with attribute access support
    from typing import Annotated as _Annotated

    class _AnnotatedAliasProxy:
        """
        Proxy returned at runtime from Annotated[Domain, "alias"].

        Provides attribute access (Buyer.id) while being usable as a type.
        """

        def __init__(self, annotated_type, domain_cls: type, alias: str):
            self._annotated_type = annotated_type
            self._domain_cls = domain_cls
            self._alias = alias

        @property
        def __name__(self):
            """Return the domain class name for compatibility."""
            return self._domain_cls.__name__

        @property
        def __module__(self):
            """Return the domain class module for compatibility."""
            return self._domain_cls.__module__

        def __getattr__(self, name: str):
            """Enable Buyer.id syntax."""
            # Avoid infinite recursion for internal attributes
            if name.startswith("_"):
                # Try to get from annotated type or domain class
                try:
                    return object.__getattribute__(self, name)
                except AttributeError:
                    raise AttributeError(name)

            from .domain import FieldProxy

            annotations = getattr(self._domain_cls, "__annotations__", {})
            if name not in annotations:
                raise AttributeError(
                    f"Domain '{self._domain_cls.__name__}' has no field '{name}'"
                )
            return FieldProxy(self._domain_cls, name, alias=self._alias)

        def __repr__(self):
            return repr(self._annotated_type)

    class _AnnotatedMeta(type):
        """Metaclass for custom Annotated that adds runtime attribute access."""

        def __getitem__(cls, params):
            """Intercept Annotated[User, "alias"] to add attribute access support."""
            # Create the standard Annotated type
            if not isinstance(params, tuple):
                params = (params,)

            standard_annotated = _Annotated[params]

            # Check if this is a domain alias (Domain class + string metadata)
            if len(params) >= 2:
                domain_cls = params[0]
                metadata = params[1] if len(params) > 1 else None

                # If metadata is a string, this is likely a domain alias
                if isinstance(metadata, str):
                    # At runtime, return a proxy that supports attribute access
                    return _AnnotatedAliasProxy(
                        standard_annotated, domain_cls, metadata
                    )

            # For non-alias Annotated, return standard
            return standard_annotated

    class Annotated(metaclass=_AnnotatedMeta):
        """
        Custom Annotated that provides attribute access for domain aliases.

        Usage:
            >>> Buyer: TypeAlias = Annotated[User, "buyer"]
            >>> Buyer.id  # Returns FieldProxy(User, "id", alias="buyer")

        For type checkers, behaves exactly like typing.Annotated.
        At runtime, domain aliases get attribute access support.
        """

        pass


from .aggregates import Aggregate
from .domain import AliasedDomainProxy, AliasedType, Domain, FieldProxy


class AnnotatedAlias:
    """
    Runtime wrapper for Annotated types that provides attribute access.

    This allows: Buyer.id to return FieldProxy(User, "id", alias="buyer")
    while keeping Buyer as a valid type annotation for mypy.
    """

    def __init__(self, domain_cls: type, alias: str):
        self._domain_cls = domain_cls
        self._alias = alias
        self._annotated_type = Annotated[domain_cls, alias]

    def __getattr__(self, name: str):
        """Intercept attribute access and return FieldProxy."""
        # Check if the attribute exists in the domain class
        annotations = getattr(self._domain_cls, "__annotations__", {})
        if name not in annotations:
            raise AttributeError(
                f"Domain '{self._domain_cls.__name__}' has no field '{name}'"
            )
        return FieldProxy(self._domain_cls, name, alias=self._alias)

    def __repr__(self):
        return f"AnnotatedAlias({self._domain_cls.__name__}, {self._alias!r})"

    # Make it compatible with isinstance checks for AliasedType
    @property
    def _annotated(self):
        return self._annotated_type


# Helper function to create annotated aliases with attribute access
def A(domain_cls: type, alias: str) -> Any:
    """
    Create an annotated domain alias that supports attribute access.

    Usage:
        >>> Buyer: TypeAlias = A(User, "buyer")
        >>> Buyer.id  # Returns FieldProxy at runtime ✓
        >>> # Use in Aggregate[Buyer, ...] ✓

    This works for both mypy and runtime:
    - Type checkers see it as Annotated[domain_cls, alias]
    - Runtime gets AnnotatedAlias with attribute access support

    Args:
        domain_cls: The Domain class to alias
        alias: The alias string

    Returns:
        An AnnotatedAlias that supports both type annotations and attribute access
    """
    if TYPE_CHECKING:
        return Annotated[domain_cls, alias]  # type: ignore
    else:
        return AnnotatedAlias(domain_cls, alias)


__all__ = [
    "A",
    "Aggregate",
    "Annotated",
    "AnnotatedAlias",
    "AliasedDomainProxy",
    "AliasedType",
    "Domain",
    "FieldProxy",
]
