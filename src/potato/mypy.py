"""
Potato Mypy Plugin - Type-safe Domain and DTO patterns with compile-time validation.

This plugin extends Pydantic's mypy plugin to provide static type checking for:
1. ViewDTO field mappings - ensures all required Domain fields are present in DTOs
2. Domain aggregate declarations - validates that referenced Domain types are declared
3. Aggregate classes - validates that all Domain fields are declared in Aggregate generics

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
    CallExpr,
    ClassDef,
    Expression,
    IndexExpr,
    MemberExpr,
    NameExpr,
    TypeInfo,
    Var,
)
from mypy.plugin import ClassDefContext, DynamicClassDefContext, MethodContext
from mypy.types import Type, TypeType, UnboundType
from pydantic.mypy import MODEL_METACLASS_FULLNAME, PydanticPlugin


class PotatoPydanticPlugin(PydanticPlugin):
    """
    Mypy plugin that validates Domain and DTO patterns at compile time.

    Extends Pydantic's mypy plugin with additional validation hooks for:
    - ViewDTO classes to ensure they properly map Domain fields
    - Domain classes to validate Aggregate type declarations
    - Aggregate classes to validate that all Domain fields are declared in generics
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
        Register hooks for custom base classes (ViewDTO, Domain, and Aggregate).

        Args:
            fullname: Fully qualified name of the base class

        Returns:
            Callback function for class validation, or None
        """
        # Check if this is a ViewDTO subclass
        if "ViewDTO" in fullname:
            return self._viewdto_class_hook
        # Check if this is a Domain subclass
        if fullname == "domain.domain.Domain":
            return self._domain_class_hook
        # Check if this is an Aggregate subclass
        if "Aggregate" in fullname:
            return self._aggregate_class_hook
        return None

    def get_method_hook(self, fullname: str) -> Callable[[MethodContext], Type] | None:
        """
        Register hooks for method calls.

        Args:
            fullname: Fully qualified name of the method

        Returns:
            Callback function for method call type inference, or None
        """
        # Hook into Domain.alias() method calls
        if fullname.endswith(".alias"):
            # Check if this is a Domain class method
            parts = fullname.rsplit(".", 1)
            if len(parts) == 2:
                class_fullname = parts[0]
                sym = self.lookup_fully_qualified(class_fullname)
                if sym and isinstance(sym.node, TypeInfo):
                    # Check multiple possible base names for Domain
                    domain_bases = ["domain.domain.Domain", "src.domain.domain.Domain"]
                    is_domain = any(sym.node.has_base(base) for base in domain_bases)
                    if is_domain:
                        return self._domain_alias_method_hook
        return None

    def get_dynamic_class_hook(
        self, fullname: str
    ) -> Callable[[DynamicClassDefContext], None] | None:
        """
        Register hooks for dynamic class creation (like User.alias()).

        This allows us to tell mypy that User.alias("buyer") creates a valid type.
        """
        # This is called when mypy sees something that might create a class dynamically
        # We want to handle Domain.alias() calls here
        if ".alias" in fullname:
            return self._domain_alias_dynamic_class_hook

        return None

    def _domain_alias_dynamic_class_hook(self, ctx: DynamicClassDefContext) -> None:
        """
        Handle Domain.alias() as a dynamic class creator.

        This tells mypy that Buyer = User.alias("buyer") creates a valid type.
        """
        # Extract the Domain class from the call expression
        # User.alias("buyer") -> call.callee is MemberExpr with expr=User, name="alias"
        if isinstance(ctx.call.callee, MemberExpr):
            domain_expr = ctx.call.callee.expr

            if isinstance(domain_expr, NameExpr) and domain_expr.node:
                if isinstance(domain_expr.node, TypeInfo):
                    domain_type_info = domain_expr.node

                    # Simply tell mypy that this variable holds the same type as the domain
                    # This is the simplest approach - Buyer is just another name for User
                    from mypy.nodes import GDEF, SymbolTableNode, TypeAlias
                    from mypy.types import Instance

                    # Create a type alias node
                    # This makes Buyer behave like User for type checking purposes
                    alias_node = TypeAlias(
                        Instance(domain_type_info, []),
                        ctx.api.qualified_name(ctx.name),
                        line=ctx.call.line,
                        column=ctx.call.column,
                    )

                    # Add it to the symbol table
                    node = SymbolTableNode(GDEF, alias_node)
                    ctx.api.add_symbol_table_node(ctx.name, node)

    def _domain_alias_method_hook(self, ctx: MethodContext) -> Type:
        """
        Handle Domain.alias() method calls to return a proper type.

        This makes Buyer = User.alias("buyer") return a type that mypy
        recognizes as valid in generic parameters.
        """
        from mypy.types import CallableType, Instance

        # When calling User.alias(), ctx.type is the callable type of User's constructor
        # We need to extract the User type itself
        if isinstance(ctx.type, CallableType):
            # The return type of the constructor is the actual class instance
            ret_type = ctx.type.ret_type
            if isinstance(ret_type, Instance):
                # Return type[Domain] so mypy sees it as a valid type
                return TypeType(ret_type)

        # Get the Domain class that alias() was called on
        if isinstance(ctx.type, TypeType):
            domain_type = ctx.type.item
            # Return type[Domain] so mypy sees it as a valid type
            return TypeType(domain_type)

        # Fallback to the default return type
        return ctx.default_return_type

    def _viewdto_class_hook(self, ctx: ClassDefContext) -> None:
        """Validate ViewDTO field mappings against Domain fields.

        ViewDTOs are allowed to include only a subset of Domain fields (partial views).
        We only validate that any field mappings point to existing Domain fields.
        """
        # Get the class definition
        cls_def: ClassDef = ctx.cls

        # Extract the Domain type from ViewDTO[Domain]
        domain_type_info = self._extract_domain_type(ctx)
        if domain_type_info is None:
            return

        # Check if the domain is an Aggregate
        is_aggregate = self._is_aggregate_type(domain_type_info)
        aggregate_domain_types = set()
        if is_aggregate:
            aggregate_domain_types = self._extract_aggregate_domain_types(domain_type_info, ctx)

        # Get all fields from the Domain(s)
        if is_aggregate:
            # For aggregates, collect fields from all domain types
            all_domain_fields = set()
            for domain_type_name in aggregate_domain_types:
                sym = ctx.api.lookup_qualified(domain_type_name, ctx.cls)
                if sym:
                    type_info = self._resolve_type_info(sym.node)
                    if type_info:
                        required_fields, optional_fields = self._get_domain_fields(type_info)
                        all_domain_fields.update(required_fields | optional_fields)
        else:
            # For regular domains, get fields from the single domain
            required_domain_fields, optional_domain_fields = self._get_domain_fields(
                domain_type_info
            )
            all_domain_fields = required_domain_fields | optional_domain_fields

        # Get field mappings from the ViewDTO (returns dict of view_field -> (domain_class, domain_field))
        view_fields, field_mappings, field_ast_nodes = self._get_view_fields_and_mappings(ctx, cls_def)

        # Validate that mapped fields exist in the correct Domain
        # ViewDTOs can include any subset of Domain fields, so we don't check for missing fields
        for view_field, (mapped_domain_class, domain_field) in field_mappings.items():
            # Get the AST node for this field to report errors on the specific field
            field_node = field_ast_nodes.get(view_field)

            # First, check if the domain class matches the ViewDTO's domain(s)
            if mapped_domain_class:
                allowed_domain_names = aggregate_domain_types if is_aggregate else {domain_type_info.name}
                if mapped_domain_class not in allowed_domain_names:
                    domain_description = f"Aggregate[{', '.join(aggregate_domain_types)}]" if is_aggregate else domain_type_info.name
                    ctx.api.fail(
                        f'ViewDTO "{cls_def.name}" field "{view_field}" maps to field from '
                        f'"{mapped_domain_class}" but ViewDTO is for "{domain_description}"',
                        field_node if field_node else ctx.cls,
                    )
                    continue

            # Then check if the field exists in the domain(s)
            if domain_field not in all_domain_fields:
                domain_description = f"Aggregate[{', '.join(aggregate_domain_types)}]" if is_aggregate else domain_type_info.name
                ctx.api.fail(
                    f'ViewDTO "{cls_def.name}" field "{view_field}" maps to '
                    f'non-existent Domain field "{domain_field}" in "{domain_description}"',
                    field_node if field_node else ctx.cls,
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

    def _is_aggregate_type(self, type_info: TypeInfo) -> bool:
        """Check if a TypeInfo represents an Aggregate class."""
        # Check if it has Aggregate in its bases
        for base in type_info.bases:
            if "Aggregate" in base.type.fullname:
                return True
        return False

    def _resolve_type_info(self, sym_node) -> TypeInfo | None:
        """Resolve a symbol node to its underlying TypeInfo, handling aliases."""
        from mypy.nodes import TypeAlias
        from mypy.types import Instance

        if isinstance(sym_node, TypeInfo):
            return sym_node
        elif isinstance(sym_node, TypeAlias):
            # For aliases, get the target type
            if isinstance(sym_node.target, Instance):
                return sym_node.target.type
        return None

    def _extract_aggregate_domain_types(self, aggregate_type_info: TypeInfo, ctx: ClassDefContext) -> set[str]:
        """
        Extract all Domain types from an Aggregate class.

        For Aggregate[User, Product], returns {'User', 'Product'}.
        """
        domain_types = set()

        # We need to look at the original AST base_type_exprs, not the resolved bases
        # But we don't have access to the Aggregate class's AST directly.
        # Instead, we can look at the aggregate_type_info's defn (definition) if available
        if aggregate_type_info.defn:
            for base_expr in aggregate_type_info.defn.base_type_exprs:
                if isinstance(base_expr, IndexExpr):
                    base = base_expr.base
                    if isinstance(base, NameExpr) and base.name == "Aggregate":
                        # Extract the types from Aggregate[Type1, Type2, ...]
                        index = base_expr.index

                        # Handle tuple of types
                        from mypy.nodes import TupleExpr

                        if isinstance(index, TupleExpr):
                            for item in index.items:
                                if isinstance(item, NameExpr):
                                    domain_types.add(item.name)
                        # Handle single type
                        elif isinstance(index, NameExpr):
                            domain_types.add(index.name)

        return domain_types

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
    ) -> tuple[set[str], dict[str, tuple[str | None, str]], dict[str, AssignmentStmt]]:
        """
        Get ViewDTO fields and their mappings to Domain fields.

        Returns:
            tuple: (set of view field names, dict mapping view field -> (domain_class, domain_field), dict mapping view field -> AST node)
                   domain_class will be None if not explicitly specified or couldn't be extracted
        """
        view_fields = set()
        field_mappings: dict[str, tuple[str | None, str]] = {}
        field_ast_nodes: dict[str, AssignmentStmt] = {}

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
                                # Store the AST node for this field
                                field_ast_nodes[field_name] = stmt

                                if type_to_check is not None:
                                    mapping = self._extract_field_proxy_mapping(
                                        type_to_check
                                    )
                                    if mapping:
                                        field_mappings[field_name] = mapping

                                # Check for Field(source=...) assignment
                                if isinstance(stmt.rvalue, CallExpr):
                                    call = stmt.rvalue
                                    # Check if calling Field
                                    if isinstance(call.callee, NameExpr) and call.callee.name == "Field":
                                        # Check arguments for 'source'
                                        source_arg = None
                                        for i, arg_name in enumerate(call.arg_names):
                                            if arg_name == "source":
                                                source_arg = call.args[i]
                                                break

                                        if source_arg:
                                            # Extract domain class and field from source arg (e.g. User.username)
                                            if isinstance(source_arg, MemberExpr):
                                                domain_class = None
                                                if isinstance(source_arg.expr, NameExpr):
                                                    domain_class = source_arg.expr.name
                                                field_mappings[field_name] = (domain_class, source_arg.name)
                                break

        return view_fields, field_mappings, field_ast_nodes

    def _extract_field_proxy_mapping(self, type_expr: Expression | Type) -> tuple[str | None, str] | None:
        """
        Extract the domain class and field name from Annotated[type, Domain.field] metadata.

        Returns a tuple of (domain_class, field_name) if found, None otherwise.
        domain_class will be None if it couldn't be extracted.
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
                        # The name might be "Domain.field" - extract domain class and field name
                        if "." in arg.name:
                            parts = arg.name.split(".")
                            if len(parts) == 2:
                                return (parts[0], parts[1])
                            return (None, parts[-1])

                    # Check if the arg is a MemberExpr (e.g., User.username)
                    elif isinstance(arg, MemberExpr):
                        domain_class = None
                        if isinstance(arg.expr, NameExpr):
                            domain_class = arg.expr.name
                        return (domain_class, arg.name)

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
                            domain_class = None
                            if isinstance(metadata.expr, NameExpr):
                                domain_class = metadata.expr.name
                            return (domain_class, metadata.name)

        return None

    def _domain_class_hook(self, ctx: ClassDefContext) -> None:
        """Validate Domain fields when using Aggregates."""
        cls_def: ClassDef = ctx.cls

        # Extract the Aggregate types from Aggregate[...]
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
                    f'Add "{domain_type_name}" to Aggregate[...] declaration or remove the reference.',
                    ctx.cls,
                )

    def _extract_aggregate_types(self, ctx: ClassDefContext) -> set[str] | None:
        """
        Extract the Domain types from Aggregate[Type1, Type2, ...] generic parameter.

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
            # print(f"DEBUG: Checking {type_name} ({sym.node.fullname}). Bases: {[b.type.fullname for b in sym.node.bases]}")
            has_base = sym.node.has_base(domain_fullname)
            if not has_base:
                 # Try checking for potato.domain.domain.Domain
                 has_base = sym.node.has_base("potato.domain.domain.Domain")
            
            if not has_base:
                 # Try checking by name only (less safe but might work for tests)
                 for base in sym.node.bases:
                     if "Domain" in base.type.fullname:
                         has_base = True
                         break
            return has_base
        return False

    def _aggregate_class_hook(self, ctx: ClassDefContext) -> None:
        """Validate Aggregate fields against declared domain types."""
        cls_def: ClassDef = ctx.cls

        # Extract the Aggregate types from Aggregate[Type1, Type2, ...]
        aggregate_types = self._extract_aggregate_types_from_aggregate(ctx)
        
        if aggregate_types is None:
            # No generic parameters, nothing to validate
            return

        # Get all Domain types referenced in fields
        referenced_domain_types = self._get_referenced_domain_types(ctx, cls_def)

        # Also get direct Domain field references (fields typed as Domain classes)
        direct_domain_fields = self._get_direct_domain_fields(ctx, cls_def)

        # Validate that all referenced Domain types are in the Aggregate
        for field_name, domain_type_name in referenced_domain_types:
            if domain_type_name not in aggregate_types:
                ctx.api.fail(
                    f'Field "{field_name}" references Domain type "{domain_type_name}" '
                    f"which is not declared in the Aggregate generic. "
                    f'Add "{domain_type_name}" to Aggregate[...] declaration or remove the reference.',
                    ctx.cls,
                )

        # Validate direct domain fields
        for field_name, domain_type_name in direct_domain_fields:
            if domain_type_name not in aggregate_types:
                ctx.api.fail(
                    f'Field "{field_name}" has type "{domain_type_name}" '
                    f"which is not declared in the Aggregate generic. "
                    f'Add "{domain_type_name}" to Aggregate[...] declaration.',
                    ctx.cls,
                )

    def _extract_aggregate_types_from_aggregate(
        self, ctx: ClassDefContext
    ) -> set[str] | None:
        """
        Extract the Domain types from Aggregate[Type1, Type2, ...] when inheriting from Aggregate.

        Returns:
            A set of type names if Aggregate is used, None otherwise.
        """
        for base_expr in ctx.cls.base_type_exprs:
            if isinstance(base_expr, IndexExpr):
                base = base_expr.base
                # Check if the base is Aggregate
                if isinstance(base, NameExpr) and base.name == "Aggregate":
                    # Get the index (the types)
                    index = base_expr.index
                    aggregate_types = set()

                    # Handle tuple of types
                    from mypy.nodes import TupleExpr

                    if isinstance(index, TupleExpr):
                        for item in index.items:
                            if isinstance(item, NameExpr):
                                aggregate_types.add(item.name)
                    # Handle single type
                    elif isinstance(index, NameExpr):
                        aggregate_types.add(index.name)

                    return aggregate_types
        return None

    def _get_direct_domain_fields(
        self, ctx: ClassDefContext, cls_def: ClassDef
    ) -> list[tuple[str, str]]:
        """
        Get all fields that are directly typed as Domain classes.

        Returns:
            A list of (field_name, domain_type_name) tuples.
        """
        direct_fields: list[tuple[str, str]] = []

        # Iterate through field assignments
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
                            domain_type = self._extract_direct_domain_type(
                                type_to_check, ctx
                            )
                            if domain_type:
                                direct_fields.append((field_name, domain_type))

        return direct_fields

    def _extract_direct_domain_type(
        self, type_expr: Expression | Type, ctx: ClassDefContext
    ) -> str | None:
        """
        Extract Domain type from a direct type annotation (not Annotated).

        Returns the Domain type name if it's a Domain class, None otherwise.
        """
        # Handle NameExpr (simple type like User)
        if isinstance(type_expr, NameExpr):
            type_name = type_expr.name
            if self._is_domain_class(type_name, ctx):
                return type_name

        # Handle UnboundType (unanalyzed types)
        if isinstance(type_expr, UnboundType):
            # Skip Annotated types - those are handled separately
            if type_expr.name == "Annotated":
                return None
            # Check if this is a Domain class
            if self._is_domain_class(type_expr.name, ctx):
                return type_expr.name

        return None


def plugin(version: str):
    # ignore version argument if the plugin works with all mypy versions.
    return PotatoPydanticPlugin
