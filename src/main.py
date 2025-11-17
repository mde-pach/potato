from __future__ import annotations

from typing import Annotated, Optional

from domain import Domain
from domain.aggregates import Aggregate
from dto import BuildDTO, ViewDTO


class User(Domain):
    id: int
    username: str
    tutor: Optional[str] = None
    friends: list[str] = []


class UserView(ViewDTO[User]):
    id: str
    login: Annotated[str, User.username]


# Incorrect mapping - would fail validation
# class IncorrectUserView(ViewDTO[User]):
#     id: str
#     login: str
# Error: missing required field "username"
# Suggested fix: use Annotated[str, User.username]


user = User(
    id=100,
    username="test",
)


class UserBuildDTO(BuildDTO[User]):
    username: str


user_build_dto = UserBuildDTO.build(user)
print(user_build_dto)

view = UserView.build(user)
print(view)

print(UserBuildDTO(username="test"))


class Price(Domain):
    amount: Annotated[int, "toto"]


class Order(Domain, Aggregate[User, Price]):
    customer: User
    price: Annotated[int, Price.amount]


Price(amount=100.0)
Order(price=100.0)

# order = Order(customer=User(id=1, username="test"), price=Price(amount=100).amount)
# print(order)
