from __future__ import annotations

from typing import Annotated, Optional

from domain import Domain
from domain.aggregates import Aggregate
from dto import BuildDTO, ViewDTO

# class User(Domain):
#     id: int
#     username: str
#     tutor: Optional[str] = None
#     friends: list[str] = []


# class UserView(ViewDTO[User]):
#     id: str
#     login: Annotated[str, User.username]


# Incorrect mapping - would fail validation
# class IncorrectUserView(ViewDTO[User]):
#     id: str
#     login: str
# Error: missing required field "username"
# Suggested fix: use Annotated[str, User.username]


# user = User(
#     id=100,
#     username="test",
# )


# class UserBuildDTO(BuildDTO[User]):
#     username: str


# user_build_dto = UserBuildDTO.build(user)
# print(user_build_dto)

# view = UserView.build(user)
# print(view)

# print(UserBuildDTO(username="test"))


class Price(Domain):
    amount: int


class User(Domain):
    id: int
    username: str
    tutor: Optional[str] = None
    friends: list[str] = []


class Order(Domain[Aggregate[User, Price]]):
    customer: User
    price: Annotated[int, Price.amount]


price = Price(amount=100.0)
user = User(id=1, username="test")

order = Order.build(user, price)
order_2 = Order(customer=user, price=price.amount)

print(order == order_2)
print(order)
print(order_2)
