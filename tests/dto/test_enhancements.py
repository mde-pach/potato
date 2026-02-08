"""Tests for v2 library enhancements."""

import pytest
from pydantic import BaseModel

from potato import (
    Domain,
    Aggregate,
    ViewDTO,
    BuildDTO,
    Field,
    Auto,
    Private,
    UNASSIGNED,
    computed,
    before_build,
    after_build,
)
from potato.core import _Unassigned


# ---------- Test Domains ----------

class Address(BaseModel):
    street: str
    city: str
    state: str


class User(Domain):
    id: Auto[int]
    username: str
    email: str
    password_hash: Private[str]


class Product(Domain):
    id: Auto[int]
    name: str
    price: float
    farmer_id: int


class Farmer(Domain):
    id: Auto[int]
    username: str
    email: str
    display_name: str
    farm_address: Address


class Permissions:
    def __init__(self, is_admin: bool = False):
        self.is_admin = is_admin


# ===== 1. Unassigned Sentinel =====

class TestUnassignedSentinel:
    """Test the UNASSIGNED sentinel for Auto fields."""

    def test_unassigned_repr(self) -> None:
        assert repr(UNASSIGNED) == "<Unassigned>"

    def test_unassigned_raises_on_str(self) -> None:
        with pytest.raises(AttributeError, match="Auto field has not been assigned"):
            str(UNASSIGNED)

    def test_unassigned_raises_on_int(self) -> None:
        with pytest.raises(AttributeError, match="Auto field has not been assigned"):
            int(UNASSIGNED)

    def test_unassigned_raises_on_float(self) -> None:
        with pytest.raises(AttributeError, match="Auto field has not been assigned"):
            float(UNASSIGNED)

    def test_unassigned_raises_on_bool(self) -> None:
        with pytest.raises(AttributeError, match="Auto field has not been assigned"):
            bool(UNASSIGNED)

    def test_unassigned_raises_on_comparison(self) -> None:
        with pytest.raises(AttributeError, match="Auto field has not been assigned"):
            UNASSIGNED < 5
        with pytest.raises(AttributeError, match="Auto field has not been assigned"):
            UNASSIGNED > 5
        with pytest.raises(AttributeError, match="Auto field has not been assigned"):
            UNASSIGNED <= 5
        with pytest.raises(AttributeError, match="Auto field has not been assigned"):
            UNASSIGNED >= 5

    def test_unassigned_raises_on_hash(self) -> None:
        with pytest.raises(AttributeError, match="Auto field has not been assigned"):
            hash(UNASSIGNED)

    def test_unassigned_eq_with_another_unassigned(self) -> None:
        other = _Unassigned()
        assert UNASSIGNED == other

    def test_unassigned_eq_with_non_unassigned_raises(self) -> None:
        with pytest.raises(AttributeError, match="Auto field has not been assigned"):
            UNASSIGNED == 5  # noqa: B015


class TestAutoFieldDefaults:
    """Test that Auto fields default to UNASSIGNED in Domain models."""

    def test_domain_auto_field_defaults_to_unassigned(self) -> None:
        user = User(username="alice", email="a@b.com", password_hash="hash")
        assert isinstance(user.id, _Unassigned)

    def test_domain_auto_field_can_be_overridden(self) -> None:
        user = User(id=42, username="alice", email="a@b.com", password_hash="hash")
        assert user.id == 42

    def test_multiple_auto_fields(self) -> None:
        from datetime import datetime, timezone

        class Article(Domain):
            id: Auto[int]
            created_at: Auto[datetime]
            title: str

        article = Article(title="Hello")
        assert isinstance(article.id, _Unassigned)
        assert isinstance(article.created_at, _Unassigned)

    def test_build_dto_to_domain_without_auto_kwargs(self) -> None:
        class UserCreate(BuildDTO[User]):
            username: str
            email: str
            password_hash: str

        dto = UserCreate(username="alice", email="a@b.com", password_hash="hash")
        user = dto.to_domain()
        assert isinstance(user.id, _Unassigned)
        assert user.username == "alice"

    def test_build_dto_to_domain_with_auto_kwargs(self) -> None:
        class UserCreate(BuildDTO[User]):
            username: str
            email: str
            password_hash: str

        dto = UserCreate(username="alice", email="a@b.com", password_hash="hash")
        user = dto.to_domain(id=42)
        assert user.id == 42


# ===== 2. Visible Fields Preserve Type =====

class TestVisibleFieldTypePreservation:
    """Test that Field(visible=...) keeps the declared type."""

    def test_visible_field_keeps_str_type(self) -> None:
        class UserView(ViewDTO[User, Permissions]):
            id: int
            username: str
            email: str = Field(visible=lambda ctx: ctx.is_admin)

        import typing
        hints = typing.get_type_hints(UserView)
        assert hints["email"] is str

    def test_visible_field_value_always_populated(self) -> None:
        class UserView(ViewDTO[User, Permissions]):
            id: int
            username: str
            email: str = Field(visible=lambda ctx: ctx.is_admin)

        user = User(id=1, username="alice", email="alice@test.com", password_hash="h")
        view = UserView.from_domain(user, context=Permissions(is_admin=False))
        # The value is still accessible on the instance
        assert view.email == "alice@test.com"

    def test_hidden_field_excluded_from_model_dump(self) -> None:
        class UserView(ViewDTO[User, Permissions]):
            id: int
            username: str
            email: str = Field(visible=lambda ctx: ctx.is_admin)

        user = User(id=1, username="alice", email="alice@test.com", password_hash="h")
        view = UserView.from_domain(user, context=Permissions(is_admin=False))
        data = view.model_dump()
        assert "email" not in data

    def test_visible_field_included_in_model_dump(self) -> None:
        class UserView(ViewDTO[User, Permissions]):
            id: int
            username: str
            email: str = Field(visible=lambda ctx: ctx.is_admin)

        user = User(id=1, username="alice", email="alice@test.com", password_hash="h")
        view = UserView.from_domain(user, context=Permissions(is_admin=True))
        data = view.model_dump()
        assert data["email"] == "alice@test.com"


# ===== 3. BuildDTO Filters Non-Domain Fields =====

class TestBuildDTOFiltering:
    """Test that to_domain() filters fields not on the domain."""

    def test_extra_fields_filtered_in_to_domain(self) -> None:
        class FarmerCreate(BuildDTO[Farmer]):
            username: str
            email: str
            display_name: str
            farm_address: Address
            password: str  # not on Farmer

        dto = FarmerCreate(
            username="alice",
            email="a@b.com",
            display_name="Alice",
            farm_address=Address(street="1 Main", city="Portland", state="OR"),
            password="secret",
        )
        farmer = dto.to_domain()
        assert farmer.username == "alice"
        assert isinstance(farmer.id, _Unassigned)  # Auto default

    def test_to_domain_override_with_extra_fields(self) -> None:
        import hashlib

        class FarmerCreate(BuildDTO[Farmer]):
            username: str
            email: str
            display_name: str
            farm_address: Address
            password: str

            def to_domain(self, **kwargs) -> Farmer:
                kwargs.setdefault(
                    "password_hash_custom",
                    hashlib.sha256(self.password.encode()).hexdigest(),
                )
                return super().to_domain(**kwargs)

        dto = FarmerCreate(
            username="alice",
            email="a@b.com",
            display_name="Alice",
            farm_address=Address(street="1 Main", city="Portland", state="OR"),
            password="secret",
        )
        # password is filtered out, and password_hash_custom is not a field,
        # but to_domain still creates the farmer without error
        farmer = dto.to_domain()
        assert farmer.username == "alice"


# ===== 4. Deep Field Path Validation =====

class TestDeepFieldPathValidation:
    """Test that deep field paths are validated at class definition time."""

    def test_valid_deep_path_works(self) -> None:
        class FarmerView(ViewDTO[Farmer]):
            city: str = Field(source=Farmer.farm_address.city)

        farmer = Farmer(
            id=1,
            username="alice",
            email="a@b.com",
            display_name="Alice",
            farm_address=Address(street="1 Main", city="Portland", state="OR"),
        )
        view = FarmerView.from_domain(farmer)
        assert view.city == "Portland"

    def test_valid_single_step_path_works(self) -> None:
        class FarmerView(ViewDTO[Farmer]):
            name: str = Field(source=Farmer.display_name)

        farmer = Farmer(
            id=1,
            username="alice",
            email="a@b.com",
            display_name="Alice",
            farm_address=Address(street="1 Main", city="Portland", state="OR"),
        )
        view = FarmerView.from_domain(farmer)
        assert view.name == "Alice"

    def test_invalid_single_step_path_raises(self) -> None:
        """Accessing a non-existent field on a Domain raises AttributeError at definition time."""
        with pytest.raises(AttributeError):
            class BadView(ViewDTO[Farmer]):
                x: str = Field(source=Farmer.nonexistent)


# ===== 5. Computed Field Error Propagation =====

class TestComputedFieldErrorPropagation:
    """Test that computed field errors propagate instead of being swallowed."""

    def test_computed_error_propagates(self) -> None:
        class SimpleUser(Domain):
            id: int
            username: str

        class UserView(ViewDTO[SimpleUser]):
            id: int
            username: str
            computed_value: str = ""

            @computed
            def computed_value(self, user: SimpleUser) -> str:  # noqa: F811
                raise ValueError("Intentional error in computed field")

        user = SimpleUser(id=1, username="alice")
        with pytest.raises(ValueError, match="Intentional error in computed field"):
            UserView.from_domain(user)

    def test_computed_field_works_normally(self) -> None:
        class SimpleUser(Domain):
            id: int
            first_name: str
            last_name: str

        class UserView(ViewDTO[SimpleUser]):
            id: int
            full_name: str = ""

            @computed
            def full_name(self, user: SimpleUser) -> str:  # noqa: F811
                return f"{user.first_name} {user.last_name}"

        user = SimpleUser(id=1, first_name="Alice", last_name="Smith")
        view = UserView.from_domain(user)
        assert view.full_name == "Alice Smith"


# ===== 6. before_build Auto-Classmethod =====

class TestBeforeBuildAutoClassmethod:
    """Test that @before_build auto-wraps as classmethod."""

    def test_before_build_without_classmethod(self) -> None:
        class SimpleUser(Domain):
            id: int
            username: str

        class UserView(ViewDTO[SimpleUser]):
            id: int
            username: str
            greeting: str = ""

            @before_build
            def enrich(cls, user: SimpleUser) -> dict:
                return {"greeting": f"Hello, {user.username}!"}

        user = SimpleUser(id=1, username="alice")
        view = UserView.from_domain(user)
        assert view.greeting == "Hello, alice!"

    def test_before_build_with_classmethod(self) -> None:
        """Backward compatible: @before_build @classmethod still works."""

        class SimpleUser(Domain):
            id: int
            username: str

        class UserView(ViewDTO[SimpleUser]):
            id: int
            username: str
            greeting: str = ""

            @before_build
            @classmethod
            def enrich(cls, user: SimpleUser) -> dict:
                return {"greeting": f"Hello, {user.username}!"}

        user = SimpleUser(id=1, username="alice")
        view = UserView.from_domain(user)
        assert view.greeting == "Hello, alice!"


# ===== 7. BuildDTO exclude= Parameter =====

class TestBuildDTOExclude:
    """Test BuildDTO exclude= parameter."""

    def test_exclude_removes_field(self) -> None:
        class ProductUpdate(BuildDTO[Product], partial=True, exclude=[Product.farmer_id]):
            name: str
            price: float

        assert "farmer_id" not in ProductUpdate.model_fields
        assert "name" in ProductUpdate.model_fields
        assert "price" in ProductUpdate.model_fields

    def test_exclude_with_string(self) -> None:
        class ProductUpdate(BuildDTO[Product], partial=True, exclude=["farmer_id"]):
            name: str
            price: float

        assert "farmer_id" not in ProductUpdate.model_fields

    def test_exclude_partial_apply_to(self) -> None:
        class ProductUpdate(BuildDTO[Product], partial=True, exclude=[Product.farmer_id]):
            name: str
            price: float

        product = Product(id=1, name="Old Name", price=5.0, farmer_id=42)
        dto = ProductUpdate(name="New Name")
        updated = dto.apply_to(product)
        assert updated.name == "New Name"
        assert updated.farmer_id == 42  # unchanged
        assert updated.price == 5.0  # unchanged (partial, unset)

    def test_exclude_without_partial(self) -> None:
        class ProductCreate(BuildDTO[Product], exclude=[Product.farmer_id]):
            name: str
            price: float

        assert "farmer_id" not in ProductCreate.model_fields
        dto = ProductCreate(name="Widget", price=9.99)
        product = dto.to_domain(farmer_id=1)
        assert product.name == "Widget"
        assert product.farmer_id == 1
