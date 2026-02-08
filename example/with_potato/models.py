"""Domain models using Potato's Domain, Aggregate, Auto, and Private."""

from datetime import datetime

from potato import Aggregate, Auto, Domain, Private


# --8<-- [start:domain]
class User(Domain):
    id: Auto[int]
    username: str
    email: str
    password_hash: Private[str]
    joined_at: Auto[datetime]


class Task(Domain):
    id: Auto[int]
    title: str
    description: str
    priority: int
    status: str
    assignee_id: int
    created_at: Auto[datetime]
# --8<-- [end:domain]


# --8<-- [start:aggregate]
class TaskAssignment(Aggregate):
    task: Task
    assignee: User
# --8<-- [end:aggregate]
