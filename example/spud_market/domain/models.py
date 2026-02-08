from datetime import datetime

from potato import Auto, Domain, Private


class FarmAddress(Domain):
    street: str
    city: str
    state: str
    zip_code: str


class Farmer(Domain):
    id: Auto[int]
    username: str
    email: str
    display_name: str
    password_hash: Private[str]
    farm_address: FarmAddress
    joined_at: Auto[datetime]


class Product(Domain):
    id: Auto[int]
    name: str
    price_per_kg: float
    description: str
    stock_kg: float
    category: str
    farmer_id: int
    listed_at: Auto[datetime]


class Order(Domain):
    id: Auto[int]
    customer_name: str
    customer_email: str
    status: str = "pending"
    placed_at: Auto[datetime]


class OrderItem(Domain):
    id: Auto[int]
    order_id: int
    product_name: str
    quantity_kg: float
    unit_price: float
