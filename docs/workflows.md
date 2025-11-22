# Developer Workflows

This guide outlines the recommended workflows for developing with Potato, including CLI tooling, testing patterns, and CI/CD integration.

## 1. The Creation Workflow

Handling entity creation is a common pattern that requires bridging the gap between "Input Data" and "Persisted Domain".

### Step 1: Define the Domain
Mark ID as a system field using `System[T]`.
```python
from potato import Domain, System

class User(Domain):
    id: System[int]
    username: str
```

### Step 2: Define the Input (BuildDTO)
The `BuildDTO` automatically excludes system fields.
```python
class CreateUser(BuildDTO[User]):
    # 'id' is excluded automatically because it's System[int]
    username: str
```

### Step 3: The Service Layer
The service persists the data and constructs the Domain.
```python
def create_user(dto: CreateUser) -> UserView:
    # 1. DTO has data (username="alice"), but no ID
    data = dto.model_dump()
    
    # 2. Service persists and gets ID (Infrastructure concern)
    user_id = db.insert(data)
    
    # 3. Domain is finally instantiated (Valid State)
    # We MUST provide system fields here
    user = dto.to_domain(id=user_id)
    
    # 4. View is returned
    return UserView.build(user)
```

## 2. CLI Tooling (Proposed)

Potato will include a CLI to scaffold DTOs and Domains, reducing boilerplate.

### Installation
```bash
pip install potato[cli]
```

### Scaffolding a New Feature
Generate a Domain, BuildDTO, and ViewDTO in one go.

```bash
potato new feature User --fields "username:str email:str"
```

## 3. Testing Workflows

Testing DTOs should be easy and consistent. We provide a `potato.testing` module to help.

### The `assert_dto_maps` Helper
Instead of writing repetitive assertions, use our helper to verify mappings.

```python
from potato.testing import assert_dto_maps

def test_user_view_mapping():
    user = User(id=1, username="alice", ...)
    
    assert_dto_maps(
        dto_cls=UserView,
        domain_instances=[user],
        expected={"display_name": "alice"}
    )
```

## 4. CI/CD Integration

### Linting & Type Checking
Enforce best practices using our custom linter plugin and mypy.

- **Rule P001**: Domain models should not be imported in API routes (use DTOs).
- **Rule P002**: ViewDTOs must be immutable.

```yaml
# .github/workflows/ci.yml
steps:
  - name: Type Check
    run: uv run mypy src
```

## 5. Best Practices

### Directory Structure
Keep DTOs close to their usage, or centralized if shared.

**Option A: Feature-based (Recommended)**
```
src/
  users/
    domain.py
    dtos.py
    service.py
```
