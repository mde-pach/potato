"""
Potato Framework Examples

This module demonstrates the key features of the Potato framework:
1. Basic Domain models
2. ViewDTO for outbound data flow (Domain → DTO)
3. BuildDTO for inbound data flow (DTO → Domain)
4. Aggregate domains with field mapping
5. Compile-time validation via mypy plugin
"""

from __future__ import annotations

from typing import Annotated, Optional, TypeAlias

from domain import Domain
from domain.aggregates import Aggregate
from dto import BuildDTO, ViewDTO

# =============================================================================
# Example 1: Basic Domain Model
# =============================================================================


class User(Domain):
    """A simple domain model with required and optional fields."""

    id: int
    username: str
    email: str
    tutor: Optional[str] = None
    friends: list[str] = []


# =============================================================================
# Example 2: ViewDTO with Field Mapping (Outbound: Domain → DTO)
# =============================================================================


class UserView(ViewDTO[User]):
    """
    A ViewDTO that maps Domain fields to different DTO field names.

    The mypy plugin validates that:
    - All required Domain fields (id, username, email) are present
    - Field mappings reference valid Domain fields
    """

    id: int
    login: Annotated[str, User.username]  # Maps 'username' → 'login'
    email: str


# Demonstrate ViewDTO usage
def example_view_dto():
    print("=" * 60)
    print("Example 2: ViewDTO with Field Mapping")
    print("=" * 60)

    user = User(id=1, username="alice", email="alice@example.com")
    view = UserView.build(user)

    print(f"Domain: {user}")
    print(f"ViewDTO: {view}")
    print(f"Field mapping: username → login = '{view.login}'")
    print()


# =============================================================================
# Example 3: ViewDTO Validation (Compile-time Error)
# =============================================================================

# Uncomment to see mypy error:
# This would fail because 'username' is missing and not mapped
#
# class IncorrectUserView(ViewDTO[User]):
#     id: int
#     email: str
#     # ERROR: Missing required field 'username'
#     # Fix: Either add 'username: str' or use 'login: Annotated[str, User.username]'


# =============================================================================
# Example 4: BuildDTO (Inbound: External Data → Domain)
# =============================================================================


class UserBuildDTO(BuildDTO[User]):
    """A BuildDTO for creating User domains from external data."""

    username: str
    email: str


def example_build_dto():
    print("=" * 60)
    print("Example 4: BuildDTO")
    print("=" * 60)

    build_dto = UserBuildDTO(username="bob", email="bob@example.com")
    user = User(**build_dto.model_dump(), id=1)
    print(f"BuildDTO: {build_dto}")
    print(f"User: {user}")
    print()


# =============================================================================
# Example 5: Aggregate Domains with Field Extraction
# =============================================================================


class Price(Domain):
    """Domain representing a price with amount and currency."""

    amount: int
    currency: str


class Product(Domain):
    """Domain representing a product."""

    id: int
    name: str
    description: str


class Order(Domain[Aggregate[User, Price, Product]]):
    """
    An aggregate domain composed of multiple other domains.

    The Aggregate declaration:
    1. Documents all domain dependencies explicitly
    2. Enables mypy to validate that all referenced domains are declared
    3. Allows automatic field extraction (e.g., Price.amount)
    """

    customer: User
    seller: User
    price_amount: Annotated[int, Price.amount]  # Extracts just the amount
    product: Product


def example_aggregate():
    print("=" * 60)
    print("Example 5: Aggregate Domains")
    print("=" * 60)

    # Create domain instances
    customer = User(id=1, username="alice", email="alice@example.com")
    seller = User(id=2, username="bob", email="bob@example.com")
    price = Price(amount=100, currency="USD")
    product = Product(id=1, name="Widget", description="A useful widget")

    # Build the aggregate
    order = Order(
        customer=customer,
        seller=seller,
        price_amount=price.amount,  # Manual extraction
        product=product,
    )

    print(f"Customer: {order.customer.username}")
    print(f"Seller: {order.seller.username}")
    print(f"Price: ${order.price_amount}")
    print(f"Product: {order.product.name}")
    print()


# =============================================================================
# Example 6: Aggregate Validation (Compile-time Error)
# =============================================================================


# Uncomment to see mypy error:
# This would fail because OtherDomain is not declared in the Aggregate
#
# class OtherDomain(Domain):
#     value: str


# class BadOrder(Domain[Aggregate[User]]):
#     user: User
#     other: Annotated[str, OtherDomain.value]
# ERROR: OtherDomain not declared in Aggregate[User]
# Fix: Change to Domain[Aggregate[User, OtherDomain]]


# =============================================================================
# Example 7: ViewDTO with Multiple Domain Instances (Aliasing)
# =============================================================================

Buyer = User.alias("buyer")
Seller = User.alias("seller")


class OrderView(ViewDTO[Aggregate[Buyer, Seller, Product]]):
    """
    A ViewDTO that combines multiple instances of the same domain type.

    This demonstrates the aliasing feature:
    - Buyer = User.alias("buyer") defines the alias - clean and discoverable!
    - Use Buyer in Aggregate[Buyer, Seller, Product]
    - Use Buyer.id syntax for field access - clean and integrated!
    - The build() method signature is: build(buyer: User, seller: User, product: Product)
    - Aliases are validated at class definition time to prevent typos
    """

    # Use Buyer.field syntax - clean and integrated!
    buyer_id: Annotated[int, Buyer.id]
    buyer_username: Annotated[str, Buyer.username]
    buyer_email: Annotated[str, Buyer.email]

    # Seller fields
    seller_id: Annotated[int, Seller.id]
    seller_username: Annotated[str, Seller.username]

    # Product fields (no alias needed - only one Product)
    product_id: Annotated[int, Product.id]
    product_name: Annotated[str, Product.name]
    product_description: Annotated[str, Product.description]


def example_aliased_view_dto():
    print("=" * 60)
    print("Example 7: ViewDTO with Aliased Domains")
    print("=" * 60)

    # Create domain instances
    buyer = User(id=1, username="alice", email="alice@example.com")
    seller = User(id=2, username="bob", email="bob@example.com")
    product = Product(id=100, name="Laptop", description="High-performance laptop")

    # Build the view with named arguments for aliased domains
    order_view = OrderView.build(buyer=buyer, seller=seller, product=product)

    print("OrderView built successfully!")
    print(f"  Buyer: {order_view.buyer_username} (ID: {order_view.buyer_id})")
    print(f"  Seller: {order_view.seller_username} (ID: {order_view.seller_id})")
    print(f"  Product: {order_view.product_name} (ID: {order_view.product_id})")
    print(f"  Product Description: {order_view.product_description}")
    print()


# =============================================================================
# Example 8: Domain Aggregates with Aliasing
# =============================================================================


class Transaction(
    Domain[Aggregate[Annotated[User, "buyer"], Annotated[User, "seller"], Product]]
):
    """
    A Domain aggregate with multiple instances of the same domain type.

    Demonstrates that aliasing works for Domain aggregates too, not just ViewDTOs.
    The Aggregate declaration specifies which aliases are used for each domain instance.
    """

    # Buyer fields
    buyer_id: Annotated[int, User("buyer").id]
    buyer_name: Annotated[str, User("buyer").username]

    # Seller fields
    seller_id: Annotated[int, User("seller").id]
    seller_name: Annotated[str, User("seller").username]

    # Product fields
    product: Product
    transaction_amount: int


def example_domain_aggregate_with_aliasing():
    print("=" * 60)
    print("Example 8: Domain Aggregates with Aliasing")
    print("=" * 60)

    # Create domain instances
    buyer = User(id=10, username="charlie", email="charlie@example.com")
    seller = User(id=20, username="diana", email="diana@example.com")
    product = Product(id=200, name="Smartphone", description="Latest model")

    # Build the transaction
    transaction = Transaction(
        buyer_id=buyer.id,
        buyer_name=buyer.username,
        seller_id=seller.id,
        seller_name=seller.username,
        product=product,
        transaction_amount=999,
    )

    print("Transaction created:")
    print(f"  From: {transaction.buyer_name} (ID: {transaction.buyer_id})")
    print(f"  To: {transaction.seller_name} (ID: {transaction.seller_id})")
    print(f"  Item: {transaction.product.name}")
    print(f"  Amount: ${transaction.transaction_amount}")
    print()


# =============================================================================
# Main Execution
# =============================================================================

if __name__ == "__main__":
    print("\n🥔 Potato Framework Examples\n")

    example_view_dto()
    example_build_dto()
    example_aggregate()
    example_aliased_view_dto()
    example_domain_aggregate_with_aliasing()

    print("=" * 60)
    print("✅ All examples completed successfully!")
    print("=" * 60)
    print("\nRun 'mypy src/main.py' to see compile-time validation in action.")
    print("Uncomment the error examples to see mypy catch issues at compile-time.")
    print()
