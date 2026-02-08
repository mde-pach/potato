# Key Concepts

Potato enforces a clear separation between your business logic and the data you send or receive from the outside world. This page explains the mental model — no code, just ideas.

## Domain Models

A **Domain** is your business truth. It contains all the fields your application needs internally — IDs, timestamps, sensitive data, relationships. Domain models can have behavior (methods) and validation rules.

Domain models are **never exposed directly** to external consumers.

## ViewDTO — Outbound Data

A **ViewDTO** transforms a domain model into an external representation. When your API returns data, it goes through a ViewDTO first.

ViewDTOs are:

- **Immutable** — once created, they can't be changed
- **Selective** — you choose which fields to expose
- **Transformable** — you can rename fields, compute new ones, or convert types

Think of ViewDTOs as a one-way lens: domain → outside world.

## BuildDTO — Inbound Data

A **BuildDTO** validates external input and converts it into a domain model. When your API receives data, it goes through a BuildDTO first.

BuildDTOs are:

- **Validated** — Pydantic validation ensures data integrity
- **Filtered** — system-managed fields (IDs, timestamps) are automatically excluded
- **Convertible** — `to_domain()` creates a domain instance, `apply_to()` updates an existing one

Think of BuildDTOs as a one-way gate: outside world → domain.

## Data Flow

Data always flows in one direction:

```
External Input ──BuildDTO──▶ Domain ──ViewDTO──▶ External Output
   (request)                 (logic)               (response)
```

This unidirectional flow means:

- Your domain can evolve without breaking API contracts
- Sensitive fields never leak into responses
- Input validation is always explicit

## Aggregates

An **Aggregate** composes multiple domain models into a single unit. When a ViewDTO needs data from several domains (e.g., an order with customer and product info), you define an aggregate.

Field names in the aggregate serve as natural namespaces — `Order.customer.username` and `Order.product.name` are unambiguous, even if both domains have an `id` field.

## Field Markers

Two special type markers control how fields flow through DTOs:

- **Auto[T]** — system-managed fields (IDs, timestamps). Excluded from BuildDTO, included in ViewDTO.
- **Private[T]** — sensitive fields (password hashes, API keys). Excluded from BuildDTO, **forbidden** in ViewDTO.

## Class-Definition-Time Validation

Potato validates your DTO definitions the moment your classes are defined — at import time, before any application code runs. If a field mapping is wrong, a private field is exposed, or a domain reference is invalid, you get an immediate error with a hint on how to fix it.

---

**Ready to code?** Start with the [Quickstart](quickstart.md) or dive into [Domain Models](../fundamentals/domain.md).
