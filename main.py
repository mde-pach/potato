from datetime import datetime

from potato import Auto, Field, Private
from potato.domain import Domain
from potato.dto import BuildDTO, ViewDTO


class User(Domain):
    id: Auto[int]
    created_at: Auto[datetime]
    username: str
    email: str
    password_hash: Private[str]


class UserCreate(BuildDTO[User]):
    username: str
    email: str


class UserView(ViewDTO[User]):
    user_id: int = Field(source=User.id)
    username: str
    email: str
