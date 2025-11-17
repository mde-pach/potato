"""Test to showcase improved error messages with various types."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from domain import Domain
from dto import ViewDTO


class Order(Domain):
    id: int
    customer_name: str
    total_amount: float
    items: list[str]
    created_at: datetime
    notes: Optional[str] = None
    is_paid: bool = False


# Missing fields to trigger errors showing actual types
# class OrderViewIncomplete(ViewDTO[Order]):
#     # Error should show: Annotated[int, Order.id]
#     # Error should show: Annotated[str, Order.customer_name]
#     # Error should show: Annotated[float, Order.total_amount]
#     # Error should show: Annotated[list[str], Order.items]
#     # Error should show: Annotated[datetime.datetime, Order.created_at]
#     pass
