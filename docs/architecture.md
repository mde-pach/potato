# Architecture & Philosophy

## Philosophy

Potato is built on the principle of **Unidirectional Data Flow** and **Compiler-Driven Development**.

### The Problem
- **Leaky Abstractions**: Returning ORM models directly exposes database schema to the API.
- **Runtime Errors**: Field renaming or refactoring often breaks API responses silently.
- **Validation Hell**: Mixing input validation logic with business rules.

### The Potato Solution
Potato enforces a hard boundary:
1.  **Inbound**: External data is validated and converted to Domain models immediately.
2.  **Core**: Business logic operates *only* on Domain models.
3.  **Outbound**: Domain models are explicitly projected into ViewDTOs for response.

## Architectural Layers

Potato fits perfectly into **Clean Architecture** or **Hexagonal Architecture**.

```mermaid
graph LR
    Client[External Client] --> BuildDTO[BuildDTO (Inbound)]
    BuildDTO --> Domain[Domain Model (Core)]
    Domain --> Logic[Business Logic]
    Logic --> Domain
    Domain --> ViewDTO[ViewDTO (Outbound)]
    ViewDTO --> Client
```

### 1. The Interface Layer (DTOs)
- **BuildDTO**: Defines the contract for *receiving* data. It handles validation, sanitization, and parsing.
- **ViewDTO**: Defines the contract for *sending* data. It handles formatting, filtering, and aggregation.

### 2. The Domain Layer
- **Domain Models**: Pure Python objects (Pydantic models) that represent your business entities. They contain no serialization logic and no external concerns.
- **System Fields**: Fields like `id` or `created_at` are marked with `System[T]`. They are integral to the Domain but managed by the infrastructure.

## Compiler-Driven Development

Potato prioritizes **Static Analysis** over runtime magic.
- **Type-based Configuration**: We use `System[int]` instead of `Field(system=True)` to leverage the type system.
- **Mypy Support**: A custom plugin validates all `Field(source=...)` references.
- **Type Safety**: Generics (`ViewDTO[User]`) ensure that you can't pass a `Product` to a `UserView`.

## Smart Injection

For computed fields, Potato uses a lightweight dependency injection mechanism based on type hints.
- **Context Injection**: If a `@computed` method requests a `context` argument matching the DTO's defined ContextType, it is automatically injected.
- **Performance**: If context is not needed, it is not passed, keeping the method signature clean and efficient.

## The Persistence Gap

A common challenge is the gap between "Creation Intent" and "Persisted State".
- **Intent**: "I want to create a user named Alice." (No ID yet).
- **State**: "A user named Alice exists with ID 1." (Has ID).

Potato solves this with **System Fields**.
- `BuildDTO[User]` automatically *excludes* `id` because it is typed as `System[int]`.
- `Domain` *requires* `id`.
- The Service Layer bridges this gap by persisting the data and providing the ID during Domain construction.
