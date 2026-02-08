# Philosophy

The design principles behind Potato.

## Domain-Driven Design

Potato models your application around **domain models** — rich business entities that contain both data and behavior. Domain models represent your business truth, independent of frameworks, databases, or APIs.

Aggregates group related domains into cohesive units. Field-based composition keeps relationships explicit and validates them at class-definition time.

## Unidirectional Data Flow

Data flows in one direction through your system:

```
External Input ──BuildDTO──▶ Domain ──ViewDTO──▶ External Output
```

- **BuildDTO → Domain**: External data is validated and converted into domain models. System fields (IDs, timestamps) are provided separately.
- **Domain → ViewDTO**: Domain models are transformed into external representations. Fields can be renamed, computed, or conditionally hidden.

This prevents coupling between your API contracts and domain structure. Each can evolve independently.

## Type Safety

Potato provides type safety at three levels:

1. **Static typing** — All DTOs and Domains use Python type hints. IDEs provide autocomplete and error detection.
2. **Class-definition-time validation** — Metaclasses validate field mappings, domain references, and private field enforcement the moment classes are defined. Errors are caught at import time.
3. **Runtime validation** — Pydantic validates data integrity when constructing BuildDTOs and domain models.

The philosophy is **fail fast**: catch errors at the earliest possible moment. A bad field mapping should never reach production.

## Immutability

ViewDTOs are frozen by default. Once created, their values cannot change. This makes data flow predictable — a ViewDTO passed to multiple consumers is guaranteed to remain consistent.

BuildDTOs and Domain models are mutable, because they need to be constructed from external data and support business logic respectively.

## Separation of Concerns

| Layer | Responsibility | Potato Type |
|-------|---------------|-------------|
| **Presentation** | API contracts, serialization | `ViewDTO`, `BuildDTO` |
| **Domain** | Business logic, rules | `Domain`, `Aggregate` |
| **Infrastructure** | Database, external services | N/A |

Dependencies flow inward: Presentation → Domain ← Infrastructure. Domain models have no dependencies on frameworks or infrastructure — they're portable and testable in isolation.

## Auto and Private Fields

Two markers separate system-managed data from user input:

- **Auto[T]**: System-managed fields (IDs, timestamps). Visible in ViewDTOs, excluded from BuildDTOs. Consumers see the full state; users don't provide system values.
- **Private[T]**: Sensitive fields (passwords, API keys). Forbidden in ViewDTOs, excluded from BuildDTOs. Potato enforces this at class-definition time — private data cannot accidentally leak.

This explicit marking makes field ownership clear at a glance.
