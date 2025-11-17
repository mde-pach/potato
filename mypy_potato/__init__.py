"""
Potato Mypy Plugin - Type-safe Domain and DTO patterns with compile-time validation.

This plugin extends Pydantic's mypy plugin to provide static type checking for:
1. ViewDTO field mappings - ensures all required Domain fields are present in DTOs
2. Domain aggregate declarations - validates that referenced Domain types are declared

The plugin enforces type safety and consistency in the unidirectional data flow
pattern between Domains and DTOs, catching configuration errors at compile-time
rather than runtime.

Usage:
    Add to mypy.ini or pyproject.toml:
    [mypy]
    plugins = mypy_potato
"""

from typing import Callable

from mypy.nodes import (
    AssignmentStmt,
    ClassDef,
    Expression,
    IndexExpr,
    MemberExpr,
    NameExpr,
    TypeInfo,
    Var,
)
from mypy.plugin import ClassDefContext
from mypy.types import Type, UnboundType
from pydantic.mypy import MODEL_METACLASS_FULLNAME, PydanticPlugin


class PotatoPydanticPlugin(PydanticPlugin):
    """
    Mypy plugin that validates Domain and DTO patterns at compile time.

    Extends Pydantic's mypy plugin with additional validation hooks for:
    - ViewDTO classes to ensure they properly map Domain fields
    - Domain classes to validate Aggregate type declarations
    """

    def get_metaclass_hook(
        self, fullname: str
    ) -> Callable[[ClassDefContext], None] | None:
        """
        Register hooks for Pydantic ModelMetaclass and its subclasses.

        Args:
            fullname: Fully qualified name of the metaclass

        Returns:
            Callback function for metaclass validation, or None
        """
        if fullname == MODEL_METACLASS_FULLNAME:
            return self._pydantic_model_metaclass_marker_callback

        # Also handle custom metaclasses that inherit from ModelMetaclass
        sym = self.lookup_fully_qualified(fullname)
        if sym and isinstance(sym.node, TypeInfo):
            if sym.node.has_base(MODEL_METACLASS_FULLNAME):
                return self._pydantic_model_metaclass_marker_callback

        return None

    def get_base_class_hook(
        self, fullname: str
    ) -> Callable[[ClassDefContext], None] | None:
        """
        Register hooks for custom base classes (ViewDTO and Domain).

        Args:
            fullname: Fully qualified name of the base class

        Returns:
            Callback function for class validation, or None
        """
        # Check if this is a ViewDTO subclass
        if fullname == "dto.ViewDTO":
            return self._viewdto_class_hook
        # Check if this is a Domain subclass
        if fullname == "domain.domain.Domain":
            return self._domain_class_hook
        return None

    def _viewdto_class_hook(self, ctx: ClassDefContext) -> None:
        """Validate ViewDTO fields against Domain fields."""
        # Get the class definition
        cls_def: ClassDef = ctx.cls

        # Extract the Domain type from ViewDTO[Domain]
        domain_type_info = self._extract_domain_type(ctx)
        if domain_type_info is None:
            return

        # Get required and optional fields from the Domain
        required_domain_fields, optional_domain_fields = self._get_domain_fields(
            domain_type_info
        )
        all_domain_fields = required_domain_fields | optional_domain_fields

        # Get all fields from the ViewDTO and their mappings
        view_fields, field_mappings = self._get_view_fields_and_mappings(ctx, cls_def)

        # Check each REQUIRED domain field is present in the view
        # Optional fields (with defaults) don't need to be in the ViewDTO
        for domain_field_name in required_domain_fields:
            # Check if field exists by name in view
            if domain_field_name in view_fields:
                continue

            # Check if field is mapped via Annotated
            if domain_field_name in field_mappings.values():
                continue

            # Field is missing! Get the type for a better error message
            field_type_str = self._get_field_type_string(
                domain_type_info, domain_field_name
            )
            ctx.api.fail(
                f'ViewDTO "{cls_def.name}" is missing required field "{domain_field_name}" '
                f'from Domain "{domain_type_info.name}". Either add a field with '
                f"the same name or use Annotated[{field_type_str}, {domain_type_info.name}.{domain_field_name}] "
                f"to map it to a different name.",
                ctx.cls,
            )

        # Validate that mapped fields exist in Domain
        for view_field, domain_field in field_mappings.items():
            if domain_field not in all_domain_fields:
                ctx.api.fail(
                    f'ViewDTO "{cls_def.name}" field "{view_field}" maps to '
                    f'non-existent Domain field "{domain_field}" in "{domain_type_info.name}"',
                    ctx.cls,
                )

    def _extract_domain_type(self, ctx: ClassDefContext) -> TypeInfo | None:
        """Extract the Domain type from ViewDTO[Domain] generic parameter."""
        # Look at the class's base classes
        for base_expr in ctx.cls.base_type_exprs:
            # Check if this is an indexed type (e.g., ViewDTO[User])
            if isinstance(base_expr, IndexExpr):
                base = base_expr.base
                # Check if the base is ViewDTO
                if isinstance(base, NameExpr) and base.name == "ViewDTO":
                    # Get the index (the Domain type parameter)
                    index = base_expr.index
                    if isinstance(index, NameExpr):
                        # Look up the type
                        sym = ctx.api.lookup_qualified(index.name, ctx.cls)
                        if sym and isinstance(sym.node, TypeInfo):
                            return sym.node
        return None

    def _get_domain_fields(
        self, domain_type_info: TypeInfo
    ) -> tuple[set[str], set[str]]:
        """
        Get all field names from a Domain model.

        Returns:
            tuple: (required fields, optional fields with defaults)
        """
        required_fields = set()
        optional_fields = set()

        # Get fields from the domain type
        for name, node in domain_type_info.names.items():
            # Skip private fields and class variables
            if name.startswith("_"):
                continue
            if isinstance(node.node, Var):
                var = node.node
                # Check if it's a model field (has a type annotation)
                if var.type is not None:
                    # Check if the field has an explicit default value
                    # has_explicit_value is True only when a field has a default like: field: int = 10
                    if var.has_explicit_value:
                        optional_fields.add(name)
                    else:
                        required_fields.add(name)

        return required_fields, optional_fields

    def _get_field_type_string(
        self, domain_type_info: TypeInfo, field_name: str
    ) -> str:
        """
        Get a string representation of a field's type from the Domain model.

        Returns:
            A formatted string representation of the type (e.g., "str", "int", "Optional[str]")
        """
        # Look up the field in the domain type
        if field_name in domain_type_info.names:
            node = domain_type_info.names[field_name]
            if isinstance(node.node, Var) and node.node.type is not None:
                # Format the type as a string
                type_str = str(node.node.type)

                # Clean up common type representations for readability
                type_str = type_str.replace("builtins.", "")
                type_str = type_str.replace("typing.", "")

                return type_str

        # Fallback if we can't determine the type
        return "Any"

    def _get_view_fields_and_mappings(
        self, ctx: ClassDefContext, cls_def: ClassDef
    ) -> tuple[set[str], dict[str, str]]:
        """
        Get ViewDTO fields and their mappings to Domain fields.

        Returns:
            tuple: (set of view field names, dict mapping view field -> domain field)
        """
        view_fields = set()
        field_mappings: dict[str, str] = {}

        # Get the TypeInfo from the class definition
        type_info = cls_def.info

        # Iterate through the names in the type info
        for field_name, sym_node in type_info.names.items():
            # Skip private fields and special attributes
            if field_name.startswith("_"):
                continue

            # Check if it's a variable (field)
            if isinstance(sym_node.node, Var):
                var = sym_node.node
                # Skip if it doesn't have a type (not a field)
                if var.type is None:
                    continue

                view_fields.add(field_name)

                # Try to extract field mapping from the type annotation
                # We need to look at the original type expression in the AST
                for stmt in cls_def.defs.body:
                    if isinstance(stmt, AssignmentStmt):
                        # AssignmentStmt has lvalues (left side) and type (annotation)
                        # Check if this assignment is for our field
                        for lvalue in stmt.lvalues:
                            if (
                                isinstance(lvalue, NameExpr)
                                and lvalue.name == field_name
                            ):
                                # Found the assignment for this field
                                # Use unanalyzed_type which has the original AST structure
                                type_to_check = (
                                    stmt.unanalyzed_type
                                    if stmt.unanalyzed_type is not None
                                    else stmt.type
                                )
                                if type_to_check is not None:
                                    domain_field = self._extract_field_proxy_mapping(
                                        type_to_check
                                    )
                                    if domain_field:
                                        field_mappings[field_name] = domain_field
                                break

        return view_fields, field_mappings

    def _extract_field_proxy_mapping(self, type_expr: Expression | Type) -> str | None:
        """
        Extract the domain field name from Annotated[type, Domain.field] metadata.

        Returns the field name if found, None otherwise.
        """
        from mypy.nodes import TupleExpr

        # Handle UnboundType (unanalyzed types)
        if isinstance(type_expr, UnboundType):
            # Check if this is Annotated
            if type_expr.name == "Annotated":
                # args[0] is the actual type, args[1:] are metadata
                for arg in type_expr.args[1:]:
                    # Check if the arg is an UnboundType (e.g., User.username)
                    if isinstance(arg, UnboundType):
                        # The name might be "Domain.field" - extract just the field name
                        if "." in arg.name:
                            return arg.name.split(".")[-1]

                    # Check if the arg is a MemberExpr (e.g., User.username)
                    elif isinstance(arg, MemberExpr):
                        return arg.name

        # Check if this is an IndexExpr (subscripted type like Annotated[...])
        elif isinstance(type_expr, IndexExpr):
            base = type_expr.base
            # Check if base is "Annotated"
            if isinstance(base, NameExpr) and base.name == "Annotated":
                # The index could be a single type or a tuple of (type, metadata...)
                index = type_expr.index

                # Handle tuple index (type, metadata1, metadata2, ...)
                if isinstance(index, TupleExpr):
                    # Skip the first item (the actual type), look at metadata
                    for metadata in index.items[1:]:
                        # Check if metadata is a MemberExpr (e.g., User.username)
                        if isinstance(metadata, MemberExpr):
                            return metadata.name

        return None

    def _domain_class_hook(self, ctx: ClassDefContext) -> None:
        """Validate Domain fields when using Aggregates."""
        cls_def: ClassDef = ctx.cls

        # Extract the Aggregate types from Domain[Aggregate[...]]
        aggregate_types = self._extract_aggregate_types(ctx)
        if aggregate_types is None:
            # No Aggregate used, nothing to validate
            return

        # Get all Domain types referenced in fields
        referenced_domain_types = self._get_referenced_domain_types(ctx, cls_def)

        # Validate that all referenced Domain types are in the Aggregate
        for field_name, domain_type_name in referenced_domain_types:
            if domain_type_name not in aggregate_types:
                ctx.api.fail(
                    f'Field "{field_name}" references Domain type "{domain_type_name}" '
                    f"which is not declared in the Aggregate generic. "
                    f'Add "{domain_type_name}" to Domain[Aggregate[...]] or remove the reference.',
                    ctx.cls,
                )

    def _extract_aggregate_types(self, ctx: ClassDefContext) -> set[str] | None:
        """
        Extract the Domain types from Domain[Aggregate[Type1, Type2, ...]] generic parameter.

        Returns:
            A set of type names if Aggregate is used, None otherwise.
        """
        for base_expr in ctx.cls.base_type_exprs:
            if isinstance(base_expr, IndexExpr):
                base = base_expr.base
                # Check if the base is Domain
                if isinstance(base, NameExpr) and base.name == "Domain":
                    # Get the index (should be Aggregate[...])
                    index = base_expr.index

                    # Check if index is Aggregate[...]
                    if isinstance(index, IndexExpr):
                        aggregate_base = index.base
                        if (
                            isinstance(aggregate_base, NameExpr)
                            and aggregate_base.name == "Aggregate"
                        ):
                            # Extract the types from Aggregate[Type1, Type2, ...]
                            aggregate_index = index.index
                            aggregate_types = set()

                            # Handle tuple of types
                            from mypy.nodes import TupleExpr

                            if isinstance(aggregate_index, TupleExpr):
                                for item in aggregate_index.items:
                                    if isinstance(item, NameExpr):
                                        aggregate_types.add(item.name)
                            # Handle single type
                            elif isinstance(aggregate_index, NameExpr):
                                aggregate_types.add(aggregate_index.name)

                            return aggregate_types
        return None

    def _get_referenced_domain_types(
        self, ctx: ClassDefContext, cls_def: ClassDef
    ) -> list[tuple[str, str]]:
        """
        Get all Domain types referenced in field annotations.

        Returns:
            A list of (field_name, domain_type_name) tuples.
        """
        referenced_types: list[tuple[str, str]] = []

        # Iterate through field assignments to find Annotated types with Domain references
        for stmt in cls_def.defs.body:
            if isinstance(stmt, AssignmentStmt):
                for lvalue in stmt.lvalues:
                    if isinstance(lvalue, NameExpr):
                        field_name = lvalue.name
                        # Check the type annotation
                        type_to_check = (
                            stmt.unanalyzed_type
                            if stmt.unanalyzed_type is not None
                            else stmt.type
                        )
                        if type_to_check is not None:
                            domain_type = self._extract_domain_type_from_annotation(
                                type_to_check, ctx
                            )
                            if domain_type:
                                referenced_types.append((field_name, domain_type))

        return referenced_types

    def _extract_domain_type_from_annotation(
        self, type_expr: Expression | Type, ctx: ClassDefContext
    ) -> str | None:
        """
        Extract Domain type from Annotated[type, Domain.field] metadata.

        Returns the Domain type name if found, None otherwise.
        """
        from mypy.nodes import TupleExpr

        # Handle UnboundType (unanalyzed types)
        if isinstance(type_expr, UnboundType):
            # Check if this is Annotated
            if type_expr.name == "Annotated":
                # args[0] is the actual type, args[1:] are metadata
                for arg in type_expr.args[1:]:
                    # Check for MemberExpr (e.g., Price.amount)
                    if isinstance(arg, MemberExpr):
                        # Get the base expression (the Domain class)
                        if isinstance(arg.expr, NameExpr):
                            domain_name = arg.expr.name
                            # Check if this is a Domain class
                            if self._is_domain_class(domain_name, ctx):
                                return domain_name
                    # Check for UnboundType with dot notation
                    elif isinstance(arg, UnboundType):
                        if "." in arg.name:
                            domain_name = arg.name.split(".")[0]
                            if self._is_domain_class(domain_name, ctx):
                                return domain_name

        # Check if this is an IndexExpr (subscripted type like Annotated[...])
        elif isinstance(type_expr, IndexExpr):
            base = type_expr.base
            # Check if base is "Annotated"
            if isinstance(base, NameExpr) and base.name == "Annotated":
                index = type_expr.index

                # Handle tuple index (type, metadata1, metadata2, ...)
                if isinstance(index, TupleExpr):
                    # Skip the first item (the actual type), look at metadata
                    for metadata in index.items[1:]:
                        # Check if metadata is a MemberExpr (e.g., Price.amount)
                        if isinstance(metadata, MemberExpr):
                            if isinstance(metadata.expr, NameExpr):
                                domain_name = metadata.expr.name
                                if self._is_domain_class(domain_name, ctx):
                                    return domain_name

        return None

    def _is_domain_class(self, type_name: str, ctx: ClassDefContext) -> bool:
        """Check if a given type name is a Domain class."""
        # Look up the type
        sym = ctx.api.lookup_qualified(type_name, ctx.cls)
        if sym and isinstance(sym.node, TypeInfo):
            # Check if it inherits from Domain
            domain_fullname = "domain.domain.Domain"
            return sym.node.has_base(domain_fullname)
        return False


def plugin(version: str):
    # ignore version argument if the plugin works with all mypy versions.
    return PotatoPydanticPlugin
