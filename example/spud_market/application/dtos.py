"""All Potato DTOs for the Spud Market application."""

import hashlib
from datetime import datetime

from potato import BuildDTO, Field, ViewDTO, before_build, after_build, computed

from example.spud_market.domain.aggregates import OrderDetail, ProductListing
from example.spud_market.domain.models import (
    Farmer,
    FarmAddress,
    Order,
    OrderItem,
    Product,
)


# ── Product DTOs ────────────────────────────────────────────────────────────


class ProductSummary(ViewDTO[Product]):
    """Compact view for product listings."""

    id: int
    name: str
    price_per_kg: float
    category: str

    @computed
    def display_price(self, product: Product) -> str:
        return f"${product.price_per_kg:.2f}/kg"


class ProductDetail(ProductSummary):
    """Extended view for single product pages."""

    description: str
    stock_kg: float
    farmer_id: int
    listed_at: str = Field(
        source=Product.listed_at,
        transform=lambda dt: dt.isoformat(),
    )

    @computed
    def in_stock(self, product: Product) -> bool:
        return product.stock_kg > 0


class ProductListingView(ViewDTO[ProductListing]):
    """Product with farmer info — for the marketplace browse page."""

    id: int = Field(source=ProductListing.product.id)
    name: str = Field(source=ProductListing.product.name)
    price_per_kg: float = Field(source=ProductListing.product.price_per_kg)
    category: str = Field(source=ProductListing.product.category)
    farmer_name: str = Field(source=ProductListing.farmer.display_name)
    farmer_city: str = Field(source=ProductListing.farmer.farm_address.city)

    @computed
    def display_price(self, agg: ProductListing) -> str:
        return f"${agg.product.price_per_kg:.2f}/kg"


class ProductCreate(BuildDTO[Product]):
    name: str
    price_per_kg: float
    description: str
    stock_kg: float
    category: str
    farmer_id: int


class ProductUpdate(BuildDTO[Product], partial=True, exclude=[Product.farmer_id]):
    name: str
    price_per_kg: float
    description: str
    stock_kg: float
    category: str


# ── Farmer DTOs ─────────────────────────────────────────────────────────────


class FarmerCreate(BuildDTO[Farmer]):
    username: str
    email: str
    display_name: str
    password: str  # not on Farmer — used in to_domain() override
    farm_address: FarmAddress

    def to_domain(self, **kwargs) -> Farmer:
        kwargs.setdefault(
            "password_hash", hashlib.sha256(self.password.encode()).hexdigest()
        )
        return super().to_domain(**kwargs)


class FarmerView(ViewDTO[Farmer]):
    id: int
    handle: str = Field(source=Farmer.username)
    display_name: str
    city: str = Field(source=Farmer.farm_address.city)
    state: str = Field(source=Farmer.farm_address.state)
    email: str = Field(visible=lambda ctx: ctx.is_admin)

    @computed
    def member_since(self, farmer: Farmer) -> str:
        return farmer.joined_at.strftime("%B %Y")


# ── Order Item DTOs ─────────────────────────────────────────────────────────


class OrderItemView(ViewDTO[OrderItem]):
    product_name: str
    quantity_kg: float
    unit_price: float

    @computed
    def line_total(self, item: OrderItem) -> float:
        return round(item.quantity_kg * item.unit_price, 2)


# ── Order DTOs ──────────────────────────────────────────────────────────────


class OrderView(ViewDTO[Order]):
    id: int
    customer_name: str
    status: str
    placed_at: str = Field(
        source=Order.placed_at,
        transform=lambda dt: dt.isoformat(),
    )


class OrderDetailView(ViewDTO[OrderDetail]):
    """Order with line items, totals, and validation."""

    order_id: int = Field(source=OrderDetail.order.id)
    customer_name: str = Field(source=OrderDetail.order.customer_name)
    customer_email: str = Field(source=OrderDetail.order.customer_email)
    status: str = Field(source=OrderDetail.order.status)
    items: list[OrderItemView]
    item_count: int
    computed_total: float

    @before_build
    def enrich(cls, entity: OrderDetail) -> dict:
        return {
            "item_count": len(entity.items),
            "computed_total": round(
                sum(i.quantity_kg * i.unit_price for i in entity.items), 2
            ),
        }

    @after_build
    def validate_total(self) -> None:
        if self.computed_total <= 0:
            raise ValueError(
                f"Order {self.order_id} has invalid total: {self.computed_total}"
            )
