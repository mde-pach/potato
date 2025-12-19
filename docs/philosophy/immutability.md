# Immutability

ViewDTOs are **frozen by default** in Potato. This immutability is a deliberate design choice that makes data flow predictable and safe.

## What is Immutability?

An immutable object cannot be modified after creation:

```python
view = UserView.build(user)
view.id = 999  # Error! ViewDTO is immutable
```

Once created, a ViewDTO's values cannot change.

## Why Immutability?

### Prevents Accidental Mutations

Without immutability, it's easy to accidentally modify data:

```python
# ❌ Bad: Mutable DTOs
def process_user(user: User) -> dict:
    view = UserView.build(user)
    view.id = 999  # Accidentally modified!
    return view.model_dump()  # Wrong data sent
```

With immutability, mutations are caught at compile time:

```python
# ✅ Good: Immutable DTOs
def process_user(user: User) -> dict:
    view = UserView.build(user)
    # view.id = 999  # Compile error - can't modify
    return view.model_dump()  # Safe
```

### Makes Data Flow Predictable

Immutability ensures data doesn't change unexpectedly:

```python
def get_user_view(user: User) -> UserView:
    view = UserView.build(user)
    # You can safely pass 'view' around
    # knowing it won't be modified
    return view
```

### Enables Safe Sharing

Immutable objects can be safely shared across boundaries:

```python
view = UserView.build(user)

# Safe to pass to multiple consumers
send_to_api(view)
log_to_analytics(view)
cache_for_later(view)

# All consumers see the same data
```

### Easier to Reason About

Immutable data is easier to understand:

```python
# With immutability, you know:
view = UserView.build(user)
# 'view' will always have the same values
# No need to worry about mutations
```

## Immutability in Practice

### ViewDTOs are Frozen

ViewDTOs are frozen by default:

```python
class UserView(ViewDTO[User]):
    id: int
    username: str

view = UserView.build(user)
view.username = "new_name"  # FrozenInstanceError!
```

### BuildDTOs are Mutable

BuildDTOs are mutable (they need to be constructed from external data):

```python
class UserCreate(BuildDTO[User]):
    username: str
    email: str

dto = UserCreate(username="alice", email="alice@example.com")
dto.username = "bob"  # OK - BuildDTOs are mutable
```

### Domain Models are Mutable

Domain models are mutable (they need to support business logic):

```python
class User(Domain):
    id: int
    username: str
    
    def activate(self) -> None:
        self.is_active = True  # OK - Domains are mutable
```

## When to Use Immutability

### ✅ Use Immutability For:

- **ViewDTOs**: Output data should not change
- **Configuration**: Settings that shouldn't be modified
- **Shared data**: Data passed between boundaries

### ❌ Don't Use Immutability For:

- **BuildDTOs**: Need to be constructed from external data
- **Domain models**: Need to support business logic mutations
- **Temporary data**: Data that needs to be modified during processing

## Immutability Patterns

### Creating New Views

Instead of modifying, create new views:

```python
# ❌ Bad: Trying to modify (won't work)
view = UserView.build(user)
view.username = "new_name"  # Error!

# ✅ Good: Create new view from domain
user.username = "new_name"  # Modify domain
view = UserView.build(user)  # Create new view
```

### Computed Fields

Use computed fields for derived data:

```python
class UserView(ViewDTO[User]):
    id: int
    username: str
    
    @computed
    def display_name(self, user: User) -> str:
        return f"@{user.username}"  # Computed, not stored
```

## Benefits Summary

Immutability provides:

- ✅ **Safety**: Prevents accidental mutations
- ✅ **Predictability**: Data doesn't change unexpectedly
- ✅ **Clarity**: Easier to reason about code
- ✅ **Concurrency**: Safe to share across threads
- ✅ **Debugging**: Easier to trace data flow

## Next Steps

- Learn about [ViewDTO](../core/viewdto.md) - see immutability in practice
- Explore [Unidirectional Data Flow](unidirectional-data-flow.md) - how immutability supports clean flow
- Understand [Type Safety](type-safety.md) - how types and immutability work together

