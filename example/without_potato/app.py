"""Demo runner — vanilla Pydantic version."""

from datetime import datetime

from .dtos import TaskCreate, TaskListView, TaskUpdate, TaskView, UserView
from .models import Task, User

# --8<-- [start:setup]
user = User(
    id=1,
    username="alice",
    email="alice@example.com",
    password_hash="hashed_secret",
    joined_at=datetime(2025, 1, 15),
)

task = Task(
    id=42,
    title="Write documentation",
    description="Add comparison page to the docs",
    priority=1,
    status="in_progress",
    assignee_id=1,
    created_at=datetime(2025, 6, 1),
)
# --8<-- [end:setup]

# --8<-- [start:view]
# ViewDTO — single object (must pass both manually)
task_view = TaskView.from_task_and_user(task, user)
print("=== Task Detail ===")
print(task_view.model_dump_json(indent=2))

# ViewDTO — batch (must build tuple pairs manually)
views = TaskListView.from_pairs([(task, user)])
print("\n=== Task List ===")
for v in views:
    print(v.model_dump_json(indent=2))

# User view
user_view = UserView.from_domain(user)
print("\n=== User ===")
print(user_view.model_dump_json(indent=2))
# --8<-- [end:view]

# --8<-- [start:build]
# BuildDTO — create
dto = TaskCreate(
    title="Review PR",
    description="Review the comparison PR",
    priority=2,
    assignee_id=1,
)
new_task = dto.to_domain(id=99, created_at=datetime(2025, 6, 2))
print("\n=== Created Task ===")
print(new_task)

# BuildDTO — partial update
update = TaskUpdate(status="done")
updated_task = update.apply_to(task)
print("\n=== Updated Task ===")
print(updated_task)
# --8<-- [end:build]
