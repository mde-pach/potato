"""FastAPI routers for the Spud Market API."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from example.spud_market.application.context import Permissions
from example.spud_market.application.dtos import (
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
from example.spud_market.application.services import (
    FarmerService,
    OrderService,
    ProductService,
)
from example.spud_market.database import get_db
from example.spud_market.infrastructure.repositories import (
    FarmerRepository,
    OrderItemRepository,
    OrderRepository,
    ProductRepository,
)


# ── Dependency injection helpers ────────────────────────────────────────────


def get_product_service(db: Session = Depends(get_db)) -> ProductService:
    return ProductService(ProductRepository(db), FarmerRepository(db))


def get_farmer_service(db: Session = Depends(get_db)) -> FarmerService:
    return FarmerService(FarmerRepository(db))


def get_order_service(db: Session = Depends(get_db)) -> OrderService:
    return OrderService(
        OrderRepository(db),
        OrderItemRepository(db),
        ProductRepository(db),
    )


# ── Product routes ──────────────────────────────────────────────────────────

product_router = APIRouter(prefix="/products", tags=["Products"])


@product_router.get("", response_model=list[ProductSummary])
def list_products(
    service: ProductService = Depends(get_product_service),
) -> list[ProductSummary]:
    return service.list_products()


@product_router.get("/listings", response_model=list[ProductListingView])
def list_product_listings(
    service: ProductService = Depends(get_product_service),
) -> list[ProductListingView]:
    """Products with farmer info for the marketplace browse page."""
    return service.list_product_listings()


@product_router.get("/{product_id}", response_model=ProductDetail)
def get_product(
    product_id: int,
    service: ProductService = Depends(get_product_service),
) -> ProductDetail:
    product = service.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@product_router.post(
    "", response_model=ProductDetail, status_code=status.HTTP_201_CREATED
)
def create_product(
    dto: ProductCreate,
    service: ProductService = Depends(get_product_service),
) -> ProductDetail:
    try:
        return service.create_product(dto)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@product_router.patch("/{product_id}", response_model=ProductDetail)
def update_product(
    product_id: int,
    dto: ProductUpdate,
    service: ProductService = Depends(get_product_service),
) -> ProductDetail:
    result = service.update_product(product_id, dto)
    if not result:
        raise HTTPException(status_code=404, detail="Product not found")
    return result


@product_router.delete(
    "/{product_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_product(
    product_id: int,
    service: ProductService = Depends(get_product_service),
) -> None:
    if not service.delete_product(product_id):
        raise HTTPException(status_code=404, detail="Product not found")


# ── Farmer routes ───────────────────────────────────────────────────────────

farmer_router = APIRouter(prefix="/farmers", tags=["Farmers"])


@farmer_router.get("", response_model=list[FarmerView])
def list_farmers(
    is_admin: bool = Query(False),
    service: FarmerService = Depends(get_farmer_service),
) -> list[FarmerView]:
    permissions = Permissions(is_admin=is_admin)
    return service.list_farmers(permissions)


@farmer_router.post(
    "", response_model=FarmerView, status_code=status.HTTP_201_CREATED
)
def create_farmer(
    dto: FarmerCreate,
    is_admin: bool = Query(False),
    service: FarmerService = Depends(get_farmer_service),
) -> FarmerView:
    permissions = Permissions(is_admin=is_admin)
    return service.create_farmer(dto, permissions)


@farmer_router.get("/{farmer_id}", response_model=FarmerView)
def get_farmer(
    farmer_id: int,
    is_admin: bool = Query(False),
    service: FarmerService = Depends(get_farmer_service),
) -> FarmerView:
    permissions = Permissions(is_admin=is_admin)
    farmer = service.get_farmer(farmer_id, permissions)
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    return farmer


# ── Order routes ────────────────────────────────────────────────────────────

order_router = APIRouter(prefix="/orders", tags=["Orders"])


class OrderItemInput(BaseModel):
    product_id: int
    quantity_kg: float


class OrderCreateInput(BaseModel):
    customer_name: str
    customer_email: str
    items: list[OrderItemInput]


@order_router.get("", response_model=list[OrderView])
def list_orders(
    service: OrderService = Depends(get_order_service),
) -> list[OrderView]:
    return service.list_orders()


@order_router.get("/{order_id}", response_model=OrderDetailView)
def get_order(
    order_id: int,
    service: OrderService = Depends(get_order_service),
) -> OrderDetailView:
    order = service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@order_router.post(
    "", response_model=OrderDetailView, status_code=status.HTTP_201_CREATED
)
def create_order(
    body: OrderCreateInput,
    service: OrderService = Depends(get_order_service),
) -> OrderDetailView:
    try:
        return service.create_order(
            customer_name=body.customer_name,
            customer_email=body.customer_email,
            items=[item.model_dump() for item in body.items],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
