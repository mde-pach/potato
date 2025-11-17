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
    def get_metaclass_hook(
        self, fullname: str
    ) -> Callable[[ClassDefContext], None] | None:
        """Update Pydantic `ModelMetaclass` definition."""
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
        """Hook for when a class inherits from a base class."""
        # Check if this is a ViewDTO subclass
        if fullname == "dto.ViewDTO":
            return self._viewdto_class_hook
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


def plugin(version: str):
    # ignore version argument if the plugin works with all mypy versions.
    return PotatoPydanticPlugin
