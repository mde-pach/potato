"""Business logic for the Spud Market."""

from datetime import datetime, timezone

from example.spud_market.domain.aggregates import OrderDetail, ProductListing
from example.spud_market.domain.models import Order, OrderItem
from example.spud_market.infrastructure.repositories import (
    FarmerRepository,
    OrderItemRepository,
    OrderRepository,
    ProductRepository,
)

from .context import Permissions
from .dtos import (
    FarmerCreate,
    FarmerView,
    OrderDetailView,
    OrderView,
    ProductCreate,
    ProductDetail,
    ProductListingView,
    ProductSummary,
    ProductUpdate,
)


class ProductService:
    def __init__(
        self, product_repo: ProductRepository, farmer_repo: FarmerRepository
    ):
        self.product_repo = product_repo
        self.farmer_repo = farmer_repo

    def list_products(self) -> list[ProductSummary]:
        products = self.product_repo.list_all()
        return ProductSummary.from_domains(products)

    def list_product_listings(self) -> list[ProductListingView]:
        """Products with farmer info for the marketplace page."""
        products = self.product_repo.list_all()
        listings = []
        for product in products:
            farmer = self.farmer_repo.get_by_id(product.farmer_id)
            if farmer:
                agg = ProductListing(product=product, farmer=farmer)
                listings.append(ProductListingView.from_domain(agg))
        return listings

    def get_product(self, product_id: int) -> ProductDetail | None:
        product = self.product_repo.get_by_id(product_id)
        if not product:
            return None
        return ProductDetail.from_domain(product)

    def create_product(self, dto: ProductCreate) -> ProductDetail:
        farmer = self.farmer_repo.get_by_id(dto.farmer_id)
        if not farmer:
            raise ValueError(f"Farmer {dto.farmer_id} not found")

        product = dto.to_domain(listed_at=datetime.now(timezone.utc))
        created = self.product_repo.create(product)
        return ProductDetail.from_domain(created)

    def update_product(
        self, product_id: int, dto: ProductUpdate
    ) -> ProductDetail | None:
        existing = self.product_repo.get_by_id(product_id)
        if not existing:
            return None
        updated = dto.apply_to(existing)
        saved = self.product_repo.update(updated)
        return ProductDetail.from_domain(saved)

    def delete_product(self, product_id: int) -> bool:
        return self.product_repo.delete(product_id)


class FarmerService:
    def __init__(self, farmer_repo: FarmerRepository):
        self.farmer_repo = farmer_repo

    def create_farmer(
        self, dto: FarmerCreate, permissions: Permissions
    ) -> FarmerView:
        farmer = dto.to_domain(joined_at=datetime.now(timezone.utc))
        created = self.farmer_repo.create(farmer)
        return FarmerView.from_domain(created, context=permissions)

    def get_farmer(
        self, farmer_id: int, permissions: Permissions
    ) -> FarmerView | None:
        farmer = self.farmer_repo.get_by_id(farmer_id)
        if not farmer:
            return None
        return FarmerView.from_domain(farmer, context=permissions)

    def list_farmers(self, permissions: Permissions) -> list[FarmerView]:
        farmers = self.farmer_repo.list_all()
        return FarmerView.from_domains(farmers, context=permissions)


class OrderService:
    def __init__(
        self,
        order_repo: OrderRepository,
        item_repo: OrderItemRepository,
        product_repo: ProductRepository,
    ):
        self.order_repo = order_repo
        self.item_repo = item_repo
        self.product_repo = product_repo

    def create_order(
        self,
        customer_name: str,
        customer_email: str,
        items: list[dict],
    ) -> OrderDetailView:
        order = Order(
            customer_name=customer_name,
            customer_email=customer_email,
            status="pending",
            placed_at=datetime.now(timezone.utc),
        )
        created_order = self.order_repo.create(order)

        order_items: list[OrderItem] = []
        for item_data in items:
            product = self.product_repo.get_by_id(item_data["product_id"])
            if not product:
                raise ValueError(f"Product {item_data['product_id']} not found")
            oi = OrderItem(
                order_id=created_order.id,
                product_name=product.name,
                quantity_kg=item_data["quantity_kg"],
                unit_price=product.price_per_kg,
            )
            order_items.append(oi)

        created_items = self.item_repo.create_many(order_items)

        agg = OrderDetail(order=created_order, items=created_items)
        return OrderDetailView.from_domain(agg)

    def get_order(self, order_id: int) -> OrderDetailView | None:
        order = self.order_repo.get_by_id(order_id)
        if not order:
            return None
        items = self.item_repo.get_for_order(order_id)
        agg = OrderDetail(order=order, items=items)
        return OrderDetailView.from_domain(agg)

    def list_orders(self) -> list[OrderView]:
        orders = self.order_repo.list_all()
        return OrderView.from_domains(orders)
