"""DTOs using Potato's ViewDTO and BuildDTO."""

from datetime import datetime

from potato import BuildDTO, Field, ViewDTO, computed

from .models import Task, TaskAssignment, User


# --8<-- [start:user-view]
class UserView(ViewDTO[User]):
    id: int
    username: str
    email: str
    joined_at: datetime
# --8<-- [end:user-view]


# --8<-- [start:task-view]
class TaskView(ViewDTO[TaskAssignment]):
    id: int = Field(source=TaskAssignment.task.id)
    title: str = Field(source=TaskAssignment.task.title)
    description: str = Field(source=TaskAssignment.task.description)
    priority: int = Field(source=TaskAssignment.task.priority)
    status: str = Field(source=TaskAssignment.task.status)
    created_at: datetime = Field(source=TaskAssignment.task.created_at)
    assignee_name: str = Field(source=TaskAssignment.assignee.username)

    @computed
    def summary(self, assignment: TaskAssignment) -> str:
        return f"[P{assignment.task.priority}] {assignment.task.title} ({assignment.task.status})"
# --8<-- [end:task-view]


# --8<-- [start:task-list-view]
class TaskListView(ViewDTO[TaskAssignment]):
    id: int = Field(source=TaskAssignment.task.id)
    title: str = Field(source=TaskAssignment.task.title)
    status: str = Field(source=TaskAssignment.task.status)
    assignee_name: str = Field(source=TaskAssignment.assignee.username)
# --8<-- [end:task-list-view]


# --8<-- [start:task-create]
class TaskCreate(BuildDTO[Task]):
    title: str
    description: str
    priority: int = 3
    status: str = "todo"
    assignee_id: int
# --8<-- [end:task-create]


# --8<-- [start:task-update]
class TaskUpdate(BuildDTO[Task], partial=True):
    title: str
    description: str
    priority: int
    status: str
    assignee_id: int
# --8<-- [end:task-update]
