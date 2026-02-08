"""Domain models using plain Pydantic — no Potato."""

from datetime import datetime

from pydantic import BaseModel


# --8<-- [start:domain]
class User(BaseModel):
    id: int
    username: str
    email: str
    password_hash: str
    joined_at: datetime


class Task(BaseModel):
    id: int
    title: str
    description: str
    priority: int
    status: str
    assignee_id: int
    created_at: datetime
# --8<-- [end:domain]


# There is no Aggregate concept — you manage multi-model
# relationships manually in every DTO classmethod.
