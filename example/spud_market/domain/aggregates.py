from potato import Aggregate

from .models import Farmer, Order, OrderItem, Product


class ProductListing(Aggregate):
    """A product with its farmer — used for marketplace listings."""

    product: Product
    farmer: Farmer


class OrderDetail(Aggregate):
    """An order with its line items — used for order detail views."""

    order: Order
    items: list[OrderItem]
