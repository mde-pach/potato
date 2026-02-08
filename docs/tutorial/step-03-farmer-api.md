# Step 3: The Farmer API

Products are live. Now let's add farmer profiles — and see how Potato protects sensitive data, maps field names, and flattens nested structures.

## The FarmerView

Here's the ViewDTO for farmers. Every line teaches something:

```python title="application/dtos.py"
from potato import ViewDTO, Field, computed


class FarmerView(ViewDTO[Farmer]):
    id: int
    handle: str = Field(source=Farmer.username)
    display_name: str
    city: str = Field(source=Farmer.farm_address.city)
    state: str = Field(source=Farmer.farm_address.state)
    email: str = Field(visible=lambda ctx: ctx.is_admin)

    @computed
    def member_since(self, farmer: Farmer) -> str:
        return farmer.joined_at.strftime("%B %Y")
```

### Field mapping — `Field(source=...)`

```python
handle: str = Field(source=Farmer.username)
```

The domain uses `username`. The API exposes `handle`. `Field(source=...)` tells Potato where to get the value. The mapping is validated at class definition time — if `Farmer.username` doesn't exist, you get an error immediately.

Fields without `Field(source=...)` are matched by name. `id`, `display_name` exist on both `Farmer` and `FarmerView`, so they auto-map.

### Deep field flattening

```python
city: str = Field(source=Farmer.farm_address.city)
state: str = Field(source=Farmer.farm_address.state)
```

`Farmer` has a nested `FarmAddress` object. The API consumer doesn't need to see that nesting — they just want `city` and `state` as flat fields. Multi-level field paths handle this: `Farmer` → `farm_address` → `city`.

This works at any depth and also works with aggregates (as we'll see in Step 4).

### Private field enforcement

Notice what's **not** in the ViewDTO: `password_hash`. It's marked `Private[str]` on the domain, so Potato forbids it in any ViewDTO. If you tried:

```python
class BadFarmerView(ViewDTO[Farmer]):
    id: int
    password_hash: str  # TypeError at class definition!
```

You'd get this error **immediately** when Python loads the class:

```
TypeError: In 'BadFarmerView', field 'password_hash' is marked as Private
in 'Farmer' and cannot be exposed in a ViewDTO.

  Hint: Remove 'password_hash' from 'BadFarmerView' or use
  'exclude=[Farmer.password_hash]' to exclude it.
```

No runtime surprise, no accidental data leak. The error fires before your app starts.

### Visibility (preview)

```python
email: str = Field(visible=lambda ctx: ctx.is_admin)
```

We'll cover this fully in [Step 5](step-05-access-control-and-errors.md), but here's the short version: `email` is only included in the serialized response when the context says `is_admin=True`. Otherwise, it's excluded from `model_dump()`. The type stays `str` (not `str | None`) — the field is always populated on the instance; visibility only affects serialization.

## Creating farmers — non-domain fields in BuildDTO

Farmers need a `password` to sign up, but the domain stores `password_hash` (a `Private` field). The BuildDTO can include fields that don't exist on the domain — `to_domain()` automatically filters them out. Override `to_domain()` to handle the conversion:

```python title="application/dtos.py"
import hashlib
from potato import BuildDTO


class FarmerCreate(BuildDTO[Farmer]):
    username: str
    email: str
    display_name: str
    password: str                # not on Farmer — kept for override
    farm_address: FarmAddress

    def to_domain(self, **kwargs) -> Farmer:
        kwargs.setdefault(
            "password_hash", hashlib.sha256(self.password.encode()).hexdigest()
        )
        return super().to_domain(**kwargs)
```

`super().to_domain()` filters out `password` (not a Farmer field), and `password_hash` comes from kwargs. Auto fields (`id`, `joined_at`) default to `UNASSIGNED` — the infrastructure layer assigns them.

## The service and routes

```python title="application/services.py"
class FarmerService:
    def __init__(self, farmer_repo: FarmerRepository):
        self.farmer_repo = farmer_repo

    def create_farmer(self, dto: FarmerCreate, permissions: Permissions) -> FarmerView:
        farmer = dto.to_domain(joined_at=datetime.now(timezone.utc))
        created = self.farmer_repo.create(farmer)
        return FarmerView.from_domain(created, context=permissions)

    def get_farmer(self, farmer_id: int, permissions: Permissions) -> FarmerView | None:
        farmer = self.farmer_repo.get_by_id(farmer_id)
        if not farmer:
            return None
        return FarmerView.from_domain(farmer, context=permissions)

    def list_farmers(self, permissions: Permissions) -> list[FarmerView]:
        farmers = self.farmer_repo.list_all()
        return FarmerView.from_domains(farmers, context=permissions)
```

The `context` parameter passes runtime information (like permissions) into the ViewDTO build process. Potato uses it for `visible` predicates and can inject it into `@computed` methods.

```python title="presentation/routers.py"
farmer_router = APIRouter(prefix="/farmers", tags=["Farmers"])


@farmer_router.get("", response_model=list[FarmerView])
def list_farmers(
    is_admin: bool = Query(False),
    service: FarmerService = Depends(get_farmer_service),
):
    permissions = Permissions(is_admin=is_admin)
    return service.list_farmers(permissions)


@farmer_router.get("/{farmer_id}", response_model=FarmerView)
def get_farmer(
    farmer_id: int,
    is_admin: bool = Query(False),
    service: FarmerService = Depends(get_farmer_service),
):
    permissions = Permissions(is_admin=is_admin)
    farmer = service.get_farmer(farmer_id, permissions)
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    return farmer
```

!!! note
    In a real app, `is_admin` would come from authentication middleware, not a query parameter. We use a query parameter here to make it easy to test both paths.

## Try it

```bash
# Public view — no email
curl "http://localhost:8000/api/farmers/1"
# {"id": 1, "handle": "green_acres", "display_name": "Green Acres Farm",
#  "city": "Portland", "state": "OR", "member_since": "March 2024"}

# Admin view — email included
curl "http://localhost:8000/api/farmers/1?is_admin=true"
# {"id": 1, "handle": "green_acres", "display_name": "Green Acres Farm",
#  "city": "Portland", "state": "OR", "email": "alice@greenacres.farm",
#  "member_since": "March 2024"}
```

Same endpoint, same ViewDTO, different output based on context. The `password_hash` is never exposed regardless of context — that's the difference between `Private` (hard boundary) and `visible` (soft, context-dependent).

!!! info "What we built"
    - Farmer list, detail, and creation endpoints
    - `FarmerView` with field mapping, deep flattening, and visibility
    - `FarmerCreate` with non-domain fields and `to_domain()` override
    - Private field enforcement preventing `password_hash` exposure

    **Potato concepts introduced:** `Field(source=...)`, deep field flattening, `Private` enforcement, `Field(visible=...)` (preview), context passing, non-domain fields in BuildDTO, `to_domain()` override

---

[:material-arrow-left: Previous: The Product API](step-02-product-api.md){ .md-button }
[Next: Step 4 — The Order API :material-arrow-right:](step-04-order-api.md){ .md-button }
