"""Tests for runtime validation (metaclass validation tests)."""

import pytest

from potato import Aggregate, Domain, Field, ViewDTO


# ============================================================================
# Valid definitions (should not raise)
# ============================================================================


def test_view_dto_field_mapping_field_class():
    class User(Domain):
        username: str

    class UserView(ViewDTO[User]):
        login: str = Field(source=User.username)


def test_view_dto_with_context():
    class UserContext:
        is_admin: bool

    class User(Domain):
        name: str

    class UserView(ViewDTO[User, UserContext]):
        name: str


def test_view_dto_automatic_field_mapping():
    class User(Domain):
        id: int
        username: str
        email: str
        is_active: bool

    class UserView(ViewDTO[User]):
        id: int
        username: str
        email: str
        is_active: bool


def test_aggregate_field_based():
    """Test new field-based aggregate definition."""
    class User(Domain):
        name: str

    class Product(Domain):
        name: str

    class Order(Aggregate):
        user: User
        product: Product
        amount: int


def test_view_dto_aggregate_with_field_source():
    """Test ViewDTO with aggregate using Field(source=...)."""
    class User(Domain):
        name: str

    class Product(Domain):
        name: str

    class Order(Aggregate):
        user: User
        product: Product

    class OrderView(ViewDTO[Order]):
        product_name: str = Field(source=Order.product.name)


def test_view_dto_aggregate_with_multiple_same_domain():
    """Test ViewDTO with aggregate having multiple fields of the same domain type."""
    class User(Domain):
        id: int
        email: str
        name: str

    class Product(Domain):
        id: int
        name: str

    class Order(Aggregate):
        buyer: User
        seller: User
        product: Product

    class OrderView(ViewDTO[Order]):
        buyer_id: int = Field(source=Order.buyer.id)
        buyer_email: str = Field(source=Order.buyer.email)
        seller_id: int = Field(source=Order.seller.id)
        seller_name: str = Field(source=Order.seller.name)


# ============================================================================
# Invalid definitions (should raise)
# ============================================================================


def test_view_dto_invalid_field_mapping():
    class User(Domain):
        name: str

    with pytest.raises(AttributeError):
        class UserView(ViewDTO[User]):
            name: str = Field(source=User.unknown)


def test_view_dto_cross_domain_field_mapping():
    class User(Domain):
        id: int
        username: str

    class Order(Domain):
        id: int
        amount: float

    with pytest.raises(TypeError, match="references"):
        class UserView(ViewDTO[User]):
            username: str
            order_id: int = Field(source=Order.id)
