"""SQLAlchemy repository implementations."""

from sqlalchemy.orm import Session

from example.spud_market.domain.models import Farmer, Order, OrderItem, Product

from .db_models import FarmerRow, OrderItemRow, OrderRow, ProductRow
from .mappers import (
    farmer_domain_to_row,
    farmer_row_to_domain,
    order_domain_to_row,
    order_item_domain_to_row,
    order_item_row_to_domain,
    order_row_to_domain,
    product_domain_to_row,
    product_row_to_domain,
)


class ProductRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, product: Product) -> Product:
        row = product_domain_to_row(product)
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return product_row_to_domain(row)

    def get_by_id(self, product_id: int) -> Product | None:
        row = self.session.get(ProductRow, product_id)
        return product_row_to_domain(row) if row else None

    def list_all(self, skip: int = 0, limit: int = 50) -> list[Product]:
        rows = (
            self.session.query(ProductRow).offset(skip).limit(limit).all()
        )
        return [product_row_to_domain(r) for r in rows]

    def update(self, product: Product) -> Product:
        row = self.session.get(ProductRow, product.id)
        if not row:
            raise ValueError(f"Product {product.id} not found")
        product_domain_to_row(product, row)
        self.session.commit()
        self.session.refresh(row)
        return product_row_to_domain(row)

    def delete(self, product_id: int) -> bool:
        row = self.session.get(ProductRow, product_id)
        if not row:
            return False
        self.session.delete(row)
        self.session.commit()
        return True


class FarmerRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, farmer: Farmer) -> Farmer:
        row = farmer_domain_to_row(farmer)
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return farmer_row_to_domain(row)

    def get_by_id(self, farmer_id: int) -> Farmer | None:
        row = self.session.get(FarmerRow, farmer_id)
        return farmer_row_to_domain(row) if row else None

    def list_all(self, skip: int = 0, limit: int = 50) -> list[Farmer]:
        rows = (
            self.session.query(FarmerRow).offset(skip).limit(limit).all()
        )
        return [farmer_row_to_domain(r) for r in rows]


class OrderRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, order: Order) -> Order:
        row = order_domain_to_row(order)
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return order_row_to_domain(row)

    def get_by_id(self, order_id: int) -> Order | None:
        row = self.session.get(OrderRow, order_id)
        return order_row_to_domain(row) if row else None

    def list_all(self, skip: int = 0, limit: int = 50) -> list[Order]:
        rows = (
            self.session.query(OrderRow).offset(skip).limit(limit).all()
        )
        return [order_row_to_domain(r) for r in rows]


class OrderItemRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, item: OrderItem) -> OrderItem:
        row = order_item_domain_to_row(item)
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return order_item_row_to_domain(row)

    def get_for_order(self, order_id: int) -> list[OrderItem]:
        rows = (
            self.session.query(OrderItemRow)
            .filter(OrderItemRow.order_id == order_id)
            .all()
        )
        return [order_item_row_to_domain(r) for r in rows]

    def create_many(self, items: list[OrderItem]) -> list[OrderItem]:
        rows = [order_item_domain_to_row(item) for item in items]
        self.session.add_all(rows)
        self.session.commit()
        for row in rows:
            self.session.refresh(row)
        return [order_item_row_to_domain(r) for r in rows]
