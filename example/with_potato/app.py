"""Demo runner — Potato version."""

from datetime import datetime

from .dtos import TaskCreate, TaskListView, TaskUpdate, TaskView, UserView
from .models import Task, TaskAssignment, User

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
# ViewDTO — single object
assignment = TaskAssignment(task=task, assignee=user)
task_view = TaskView.from_domain(assignment)
print("=== Task Detail ===")
print(task_view.model_dump_json(indent=2))

# ViewDTO — batch
views = TaskListView.from_domains([assignment])
print("\n=== Task List ===")
for v in views:
    print(v.model_dump_json(indent=2))

# User view (password_hash is Private — can't appear here)
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
