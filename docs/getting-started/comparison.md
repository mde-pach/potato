# Potato vs Vanilla Pydantic

Both examples below solve the **exact same problem** — a task-management API with users, tasks, and an aggregate view that joins the two. One uses Potato, the other uses plain Pydantic. The runtime output is identical; the difference is how much you have to write and maintain.

---

## Domain Models

=== "With Potato"

    ```python
    --8<-- "example/with_potato/models.py:domain"
    ```

    `Auto[int]` and `Auto[datetime]` mark infrastructure-managed fields.
    `Private[str]` marks fields that must **never** appear in any ViewDTO — enforced at class-definition time.

=== "Without Potato"

    ```python
    --8<-- "example/without_potato/models.py:domain"
    ```

    Every field is a plain type. Nothing distinguishes auto-generated fields from
    user-supplied ones, and nothing prevents `password_hash` from leaking into a response DTO.

---

## Aggregates

=== "With Potato"

    ```python
    --8<-- "example/with_potato/models.py:aggregate"
    ```

    The `Aggregate` base class lets you compose domains. Field names become
    namespaces for DTO mapping — `TaskAssignment.task.title`,
    `TaskAssignment.assignee.username`.

=== "Without Potato"

    There is no aggregate concept. You pass multiple objects around manually
    and wire them together in every classmethod.

---

## ViewDTO — Outbound Data

=== "With Potato"

    ```python
    --8<-- "example/with_potato/dtos.py:user-view"
    ```

    ```python
    --8<-- "example/with_potato/dtos.py:task-view"
    ```

    Fields are declared once. `Field(source=...)` maps across aggregate
    boundaries. `@computed` derives new fields from the domain. No classmethods, no manual wiring.

=== "Without Potato"

    ```python
    --8<-- "example/without_potato/dtos.py:user-view"
    ```

    ```python
    --8<-- "example/without_potato/dtos.py:task-view"
    ```

    Every DTO needs a hand-written `from_domain` / `from_task_and_user`
    classmethod that maps each field individually. If a domain field is
    renamed, the classmethod silently breaks at runtime.

---

## BuildDTO — Inbound Data

=== "With Potato"

    ```python
    --8<-- "example/with_potato/dtos.py:task-create"
    ```

    ```python
    --8<-- "example/with_potato/dtos.py:task-update"
    ```

    `Auto` fields (`id`, `created_at`) are excluded automatically.
    `partial=True` makes every field optional — no duplication.

=== "Without Potato"

    ```python
    --8<-- "example/without_potato/dtos.py:task-create"
    ```

    ```python
    --8<-- "example/without_potato/dtos.py:task-update"
    ```

    You must remember to exclude `id` and `created_at` yourself.
    For partial updates, every field must be manually re-declared as
    `T | None = None`.

---

## Using It

=== "With Potato"

    ```python
    --8<-- "example/with_potato/app.py:view"
    ```

    ```python
    --8<-- "example/with_potato/app.py:build"
    ```

=== "Without Potato"

    ```python
    --8<-- "example/without_potato/app.py:view"
    ```

    ```python
    --8<-- "example/without_potato/app.py:build"
    ```

---

## Line Count

| File | With Potato | Without Potato |
|---|:-:|:-:|
| `models.py` | 20 | 19 |
| `dtos.py` | 37 | 90 |
| `app.py` | 49 | 48 |
| **Total** | **106** | **157** |

The DTO layer — where the real complexity lives — is **less than half** the size with Potato.

---

## What Potato Catches at Definition Time

These errors are raised the moment Python imports the class, not at runtime when a request hits:

- **Private field in ViewDTO** — `Private[str]` fields cannot be added to any ViewDTO. If you try, you get a `TypeError` at import time.
- **Invalid field mapping** — `Field(source=User.nonexistent)` raises immediately.
- **Missing domain field** — declaring a field name that doesn't exist on the domain is caught before any request.
- **Deep path validation** — `Field(source=Order.customer.address.city)` validates every step of the path at class definition.

With vanilla Pydantic, all of these are silent bugs that surface only when exercised at runtime — if ever.

---

## Summary

| | With Potato | Without Potato |
|---|---|---|
| Computed fields | `@computed` decorator | Inline in classmethod |
| Field mapping | Declarative `Field(source=...)` | Manual in every classmethod |
| Batch conversion | `.from_domains(list)` | Hand-written list comprehension |
| Auto field exclusion | Automatic in BuildDTO | Must remember manually |
| Partial updates | `partial=True` + `apply_to()` | Re-declare every field as `T \| None = None` |
| Private field safety | Enforced at import time | Nothing prevents leaking |
| Aggregates | First-class `Aggregate` type | No concept — manual wiring |
| Error detection | Class-definition time | Runtime (if ever) |
