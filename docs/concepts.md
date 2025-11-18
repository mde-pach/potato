# Core Concepts

This guide explains the foundational concepts behind Potato: Domain-Driven Design (DDD), Data Transfer Objects (DTOs), and unidirectional data flow.

## Domain-Driven Design (DDD)

Domain-Driven Design is a software development approach that focuses on modeling software to match a domain according to input from domain experts.

### Domain Models

A **domain model** represents a concept from your business domain. It encapsulates both data and behavior related to that concept. In Potato, domain models are the core entities of your application.

```python
class User(Domain):
    id: int
    username: str
    email: str
    created_at: datetime
```

Domain models should:
- Represent business concepts, not database tables or API schemas
- Contain business logic and validation rules
- Be independent of external systems (databases, APIs, UIs)

### Aggregates

An **aggregate** is a cluster of domain objects that are treated as a single unit. Aggregates help maintain consistency boundaries in your domain.

In Potato, aggregates are domains that compose multiple other domains:

```python
class Order(Domain[Aggregate[User, Product, Price]]):
    customer: User
    product: Product
    total: Annotated[int, Price.amount]
```

### Bounded Contexts

A **bounded context** defines the limits of a particular domain model. The same concept (like "User") might have different representations in different contexts (e.g., "Customer" in sales, "Employee" in HR).

Potato helps you maintain clear boundaries by enforcing separation between domain models and their external representations.

## Data Transfer Objects (DTOs)

A **Data Transfer Object (DTO)** is an object that carries data between processes or layers. DTOs have no behavior except for storage and retrieval of data.

### Why Use DTOs?

1. **Separation of Concerns**: Your domain models don't need to match external API contracts
2. **Versioning**: You can evolve your domain models independently from API schemas
3. **Security**: Control exactly what data is exposed externally
4. **Performance**: Transfer only the data you need

### DTO Patterns

There are two main DTO patterns:

- **Input DTOs**: Transform external data into domain models
- **Output DTOs**: Transform domain models into external representations

Potato enforces this separation with two distinct types: `BuildDTO` and `ViewDTO`.

## Unidirectional Data Flow

Unidirectional data flow means data moves in one direction through your application layers. This makes data transformations predictable and easier to reason about.

### The Flow

```
External System → BuildDTO → Domain Model → ViewDTO → External System
```

1. **Inbound (BuildDTO)**: External data enters your system
   - API requests, form submissions, database records
   - Validated and transformed into domain models
   - Example: `CreateUser` DTO → `User` domain

2. **Domain Layer**: Your business logic operates here
   - Domain models contain business rules
   - Operations are performed on domain models
   - Example: `User` domain with business methods

3. **Outbound (ViewDTO)**: Domain models are transformed for external consumption
   - API responses, serialized data, UI models
   - Domain models are transformed into DTOs
   - Example: `User` domain → `UserView` DTO

### Benefits

- **Predictability**: Data always flows in one direction
- **Testability**: Each transformation can be tested independently
- **Maintainability**: Changes to external contracts don't affect domain models
- **Type Safety**: Compile-time validation ensures correct data flow

## Potato's Opinionated Approach

Potato makes several opinionated choices to enforce best practices:

### 1. Separate Input and Output DTOs

Potato provides two distinct base classes:
- `BuildDTO[D]`: For constructing domain models from external data
- `ViewDTO[D]`: For creating external representations from domain models

This separation prevents accidentally using the wrong DTO type and makes data flow explicit.

### 2. Immutable ViewDTOs

`ViewDTO` instances are **frozen** (immutable) by default. This prevents accidental mutations of data that's meant to be read-only:

```python
view = UserView.build(user)
view.username = "hacker"  # ❌ Raises ValidationError
```

### 3. Type-Safe Field Mapping

Potato uses Python's type system to ensure field mappings are correct at compile time:

```python
class UserView(ViewDTO[User]):
    login: Annotated[str, User.username]  # ✅ Type-checked
```

### 4. Explicit Aggregate Declarations

Aggregates must explicitly declare their dependencies:

```python
class Order(Domain[Aggregate[User, Product, Price]]):
    # All referenced domains must be in Aggregate[...]
```

This makes dependencies clear and enables compile-time validation.

### 5. Domain Aliasing for Multiple Instances

When you need multiple instances of the same domain type, aliasing makes it explicit:

```python
Buyer = User.alias("buyer")
Seller = User.alias("seller")

class TransactionView(ViewDTO[Aggregate[Buyer, Seller, Product]]):
    buyer_name: Annotated[str, Buyer.username]
    seller_name: Annotated[str, Seller.username]
```

## When to Use Potato

Potato is ideal when:

- ✅ You need clear separation between domain models and external APIs
- ✅ You want compile-time validation of data transformations
- ✅ You're building APIs that need to evolve independently
- ✅ You want to prevent accidental coupling between layers
- ✅ You need to handle complex aggregates with multiple domain types

Potato might not be the right choice when:

- ❌ You have simple CRUD applications with 1:1 domain-to-API mapping
- ❌ You don't need strict boundaries between layers
- ❌ You're prototyping and need maximum flexibility

## Next Steps

Now that you understand the concepts, let's build something:

- **[Quickstart Guide](quickstart.md)** - Build your first DTOs
- **[Domain Models](core/domain.md)** - Learn about creating domain models
- **[ViewDTO](core/viewdto.md)** - Create output DTOs
- **[BuildDTO](core/builddto.md)** - Create input DTOs

