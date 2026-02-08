"""Bidirectional mapping between Potato domain models and SQLAlchemy rows."""

from example.spud_market.domain.models import (
    FarmAddress,
    Farmer,
    Order,
    OrderItem,
    Product,
)

from .db_models import FarmerRow, OrderItemRow, OrderRow, ProductRow


# ── Farmer ──────────────────────────────────────────────────────────────────


def farmer_row_to_domain(row: FarmerRow) -> Farmer:
    return Farmer(
        id=row.id,
        username=row.username,
        email=row.email,
        display_name=row.display_name,
        password_hash=row.password_hash,
        farm_address=FarmAddress(
            street=row.street,
            city=row.city,
            state=row.state,
            zip_code=row.zip_code,
        ),
        joined_at=row.joined_at,
    )


def farmer_domain_to_row(farmer: Farmer, row: FarmerRow | None = None) -> FarmerRow:
    if row is None:
        row = FarmerRow()
    row.username = farmer.username
    row.email = farmer.email
    row.display_name = farmer.display_name
    row.password_hash = farmer.password_hash
    row.street = farmer.farm_address.street
    row.city = farmer.farm_address.city
    row.state = farmer.farm_address.state
    row.zip_code = farmer.farm_address.zip_code
    return row


# ── Product ─────────────────────────────────────────────────────────────────


def product_row_to_domain(row: ProductRow) -> Product:
    return Product(
        id=row.id,
        name=row.name,
        price_per_kg=row.price_per_kg,
        description=row.description,
        stock_kg=row.stock_kg,
        category=row.category,
        farmer_id=row.farmer_id,
        listed_at=row.listed_at,
    )


def product_domain_to_row(
    product: Product, row: ProductRow | None = None
) -> ProductRow:
    if row is None:
        row = ProductRow()
    row.name = product.name
    row.price_per_kg = product.price_per_kg
    row.description = product.description
    row.stock_kg = product.stock_kg
    row.category = product.category
    row.farmer_id = product.farmer_id
    return row


# ── Order ───────────────────────────────────────────────────────────────────


def order_row_to_domain(row: OrderRow) -> Order:
    return Order(
        id=row.id,
        customer_name=row.customer_name,
        customer_email=row.customer_email,
        status=row.status,
        placed_at=row.placed_at,
    )


def order_domain_to_row(order: Order, row: OrderRow | None = None) -> OrderRow:
    if row is None:
        row = OrderRow()
    row.customer_name = order.customer_name
    row.customer_email = order.customer_email
    row.status = order.status
    return row


# ── OrderItem ───────────────────────────────────────────────────────────────


def order_item_row_to_domain(row: OrderItemRow) -> OrderItem:
    return OrderItem(
        id=row.id,
        order_id=row.order_id,
        product_name=row.product_name,
        quantity_kg=row.quantity_kg,
        unit_price=row.unit_price,
    )


def order_item_domain_to_row(
    item: OrderItem, row: OrderItemRow | None = None
) -> OrderItemRow:
    if row is None:
        row = OrderItemRow()
    row.order_id = item.order_id
    row.product_name = item.product_name
    row.quantity_kg = item.quantity_kg
    row.unit_price = item.unit_price
    return row
