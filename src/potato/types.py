

class FieldProxy:
    """
    Proxy object for referencing fields from a Domain model.

    Supports chained access for deep flattening:
        User.address.city → FieldProxy(User, "city", path=["address", "city"])

    Attributes:
        model_cls: The Domain class being referenced
        field_name: The leaf field name
        namespace: Aggregate field name used as namespace (e.g., "author" in PostAggregate)
        path: Full dotted path for deep access (e.g., ["address", "city"])
    """

    def __init__(
        self,
        model_cls: type,
        field_name: str,
        namespace: str | None = None,
        path: list[str] | None = None,
    ):
        self.model_cls = model_cls
        self.field_name = field_name
        self.namespace = namespace
        self.path = path or [field_name]

    def __getattr__(self, name: str) -> "FieldProxy":
        """Support chained field access for deep flattening (e.g., User.address.city)."""
        # Resolve the type of the current leaf field to validate chaining
        current_cls = self.model_cls
        resolved_type = None

        # Walk the path to find the type of the leaf
        try:
            import typing
            for step in self.path:
                hints = typing.get_type_hints(current_cls)
                if step in hints:
                    resolved_type = hints[step]
                    # Unwrap Optional, etc.
                    origin = typing.get_origin(resolved_type)
                    if origin is not None:
                        args = typing.get_args(resolved_type)
                        if args:
                            resolved_type = args[0]
                    current_cls = resolved_type
                else:
                    break
        except Exception:
            pass

        # Check if the resolved type has the requested attribute as an annotation
        if resolved_type is not None and hasattr(resolved_type, "__annotations__"):
            annotations = resolved_type.__annotations__
            if name in annotations:
                return FieldProxy(
                    model_cls=self.model_cls,
                    field_name=name,
                    namespace=self.namespace,
                    path=self.path + [name],
                )

        raise AttributeError(
            f"Cannot chain '.{name}' on {self!r}: "
            f"the resolved type does not have field '{name}'"
        )

    def __repr__(self) -> str:
        parts = []
        if self.namespace:
            parts.append(f"namespace={self.namespace!r}")
        path_str = ".".join(self.path)
        return f"FieldProxy({self.model_cls.__name__}.{path_str})"


class DomainFieldAccessor:
    """
    Proxy returned by Aggregate.__getattr__ for Domain-typed fields.

    Allows accessing domain fields through the aggregate namespace:
        PostAggregate.author.username → FieldProxy(User, "username", namespace="author")
    """

    def __init__(self, domain_cls: type, namespace: str):
        self.domain_cls = domain_cls
        self.namespace = namespace

    def __getattr__(self, name: str) -> FieldProxy:
        """Return a FieldProxy with the namespace attached."""
        annotations = getattr(self.domain_cls, "__annotations__", {})
        # Also check parent annotations for inherited fields
        for base in getattr(self.domain_cls, "__mro__", []):
            if name in getattr(base, "__annotations__", {}):
                return FieldProxy(self.domain_cls, name, namespace=self.namespace, path=[name])
        if name in annotations:
            return FieldProxy(self.domain_cls, name, namespace=self.namespace, path=[name])
        raise AttributeError(
            f"Domain '{self.domain_cls.__name__}' has no field '{name}'"
        )

    def __repr__(self) -> str:
        return f"DomainFieldAccessor({self.domain_cls.__name__}, namespace={self.namespace!r})"
