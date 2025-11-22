"""Tests for the Mypy plugin."""

def test_view_dto_field_mapping_annotated(assert_mypy_output):
    code = """
from typing import Annotated
from potato import Domain, ViewDTO

class User(Domain):
    username: str

class UserView(ViewDTO[User]):
    # Map username to login
    login: Annotated[str, User.username]
"""
    assert_mypy_output(code, expected_clean=True)

def test_view_dto_field_mapping_field_class(assert_mypy_output):
    code = """
from potato import Domain, ViewDTO, Field

class User(Domain):
    username: str

class UserView(ViewDTO[User]):
    # Map username to login using Field
    login: str = Field(source=User.username)
"""
    assert_mypy_output(code, expected_clean=True)

def test_view_dto_with_context(assert_mypy_output):
    code = """
from potato import Domain, ViewDTO

class UserContext:
    is_admin: bool

class User(Domain):
    name: str

class UserView(ViewDTO[User, UserContext]):
    name: str
"""
    assert_mypy_output(code, expected_clean=True)

def test_view_dto_invalid_field_mapping(assert_mypy_output):
    code = """
from potato import Domain, ViewDTO, Field

class User(Domain):
    name: str

class UserView(ViewDTO[User]):
    # 'unknown' does not exist on User
    name: str = Field(source=User.unknown)
"""
    # We check for our plugin's error message specifically.
    assert_mypy_output(code, expected_errors=['ViewDTO "UserView" field "name" maps to non-existent Domain field "unknown" in "User"'])

def test_view_dto_cross_domain_field_mapping(assert_mypy_output):
    code = """
from potato import Domain, ViewDTO, Field

class User(Domain):
    id: int
    username: str

class Order(Domain):
    id: int
    amount: float

# Should error - mapping to Order.id in ViewDTO[User]
class UserView(ViewDTO[User]):
    username: str
    order_id: int = Field(source=Order.id)
"""
    # This should detect that Order.id is from the wrong domain
    assert_mypy_output(code, expected_errors=['ViewDTO "UserView" field "order_id" maps to field from "Order" but ViewDTO is for "User"'])


def test_aggregate_validation_missing_domain(assert_mypy_output):
    code = """
from potato import Domain, Aggregate

class User(Domain):
    name: str

class Order(Domain):
    amount: int

# Order is used but not declared in Aggregate
class MyAggregate(Aggregate[User]):
    user: User
    order: Order
"""
    assert_mypy_output(code, expected_errors=['Field "order" has type "Order" which is not declared in the Aggregate generic'])

def test_domain_aliasing(assert_mypy_output):
    code = """
from potato import Domain, Aggregate

class User(Domain):
    name: str

# This should be valid and inferred as a type
Buyer = User.alias("buyer")

class MyAggregate(Aggregate[User, Buyer]):
    user: User
    buyer: Buyer
"""
    assert_mypy_output(code, expected_clean=True)
