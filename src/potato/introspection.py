from .types import FieldProxy


def extract_field_mappings(cls: type) -> dict[str, tuple[type, str, str | None, list[str]]]:
    """
    Extract field mappings from Field(source=...) declarations.

    Returns:
        A dictionary mapping field names to (domain_class, field_name, namespace, path) tuples.
    """
    field_mappings: dict[str, tuple[type, str, str | None, list[str]]] = {}

    if hasattr(cls, "__potato_fields__"):
        for field_name, field_def in cls.__potato_fields__.items():
            if field_def.source:
                if isinstance(field_def.source, FieldProxy):
                    field_mappings[field_name] = (
                        field_def.source.model_cls,
                        field_def.source.field_name,
                        field_def.source.namespace,
                        field_def.source.path,
                    )

    return field_mappings
