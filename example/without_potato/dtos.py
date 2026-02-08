"""DTOs using plain Pydantic — no Potato."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from .models import Task, User


# --8<-- [start:user-view]
class UserView(BaseModel):
    model_config = {"frozen": True}

    id: int
    username: str
    email: str
    joined_at: datetime

    @classmethod
    def from_domain(cls, user: User) -> UserView:
        return cls(
            id=user.id,
            username=user.username,
            email=user.email,
            joined_at=user.joined_at,
            # Bug risk: nothing prevents adding password_hash here
        )

    @classmethod
    def from_domains(cls, users: list[User]) -> list[UserView]:
        return [cls.from_domain(u) for u in users]
# --8<-- [end:user-view]


# --8<-- [start:task-view]
class TaskView(BaseModel):
    model_config = {"frozen": True}

    id: int
    title: str
    description: str
    priority: int
    status: str
    created_at: datetime
    assignee_name: str
    summary: str

    @classmethod
    def from_task_and_user(cls, task: Task, user: User) -> TaskView:
        return cls(
            id=task.id,
            title=task.title,
            description=task.description,
            priority=task.priority,
            status=task.status,
            created_at=task.created_at,
            assignee_name=user.username,
            summary=f"[P{task.priority}] {task.title} ({task.status})",
        )

    @classmethod
    def from_pairs(
        cls, pairs: list[tuple[Task, User]]
    ) -> list[TaskView]:
        return [cls.from_task_and_user(t, u) for t, u in pairs]
# --8<-- [end:task-view]


# --8<-- [start:task-list-view]
class TaskListView(BaseModel):
    model_config = {"frozen": True}

    id: int
    title: str
    status: str
    assignee_name: str

    @classmethod
    def from_task_and_user(cls, task: Task, user: User) -> TaskListView:
        return cls(
            id=task.id,
            title=task.title,
            status=task.status,
            assignee_name=user.username,
        )

    @classmethod
    def from_pairs(
        cls, pairs: list[tuple[Task, User]]
    ) -> list[TaskListView]:
        return [cls.from_task_and_user(t, u) for t, u in pairs]
# --8<-- [end:task-list-view]


# --8<-- [start:task-create]
class TaskCreate(BaseModel):
    title: str
    description: str
    priority: int = 3
    status: str = "todo"
    assignee_id: int
    # Must manually remember to exclude id and created_at

    def to_domain(self, **kwargs: object) -> Task:
        return Task(**self.model_dump(), **kwargs)
# --8<-- [end:task-create]


# --8<-- [start:task-update]
class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    priority: int | None = None
    status: str | None = None
    assignee_id: int | None = None
    # Every field must be manually declared Optional with default None

    def apply_to(self, task: Task) -> Task:
        data = task.model_dump()
        updates = {k: v for k, v in self.model_dump().items() if v is not None}
        data.update(updates)
        return Task(**data)
# --8<-- [end:task-update]
