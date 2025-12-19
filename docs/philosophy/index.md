# Philosophy

Understanding the foundational principles behind Potato will help you build better applications. This section explores the core philosophies that guide Potato's design and implementation.

## Core Principles

### [Domain-Driven Design](domain-driven-design.md)

Potato is inspired by Domain-Driven Design (DDD) principles. Learn how DDD helps you model your business domain accurately, maintain consistency through ubiquitous language, and define clear boundaries between different parts of your system.

**Key concepts:** Domain models, ubiquitous language, bounded contexts

### [Data Transfer Objects](data-transfer-objects.md)

DTOs are simple structures for transferring data between layers. Understand why DTOs are essential for clean architecture, how they differ from domain models, and when to use BuildDTOs vs ViewDTOs.

**Key concepts:** Pure data structures, immutability, single purpose

### [Unidirectional Data Flow](unidirectional-data-flow.md)

Potato enforces unidirectional data flow: external data flows in through BuildDTOs, through your domain logic, and out through ViewDTOs. This creates predictable, traceable data transformations.

**Key concepts:** Inbound flow, outbound flow, clear boundaries

### [Type Safety](type-safety.md)

Potato provides compile-time type safety through static typing, runtime validation, and a Mypy plugin. Catch errors before they reach production and improve code quality through type checking.

**Key concepts:** Static typing, runtime validation, compile-time checking

### [Immutability](immutability.md)

ViewDTOs are frozen by default, preventing accidental mutations and making data flow predictable. Learn why immutability matters and how it enables safe data sharing across boundaries.

**Key concepts:** Frozen objects, predictable data flow, safe sharing

### [System Fields](system-fields.md)

`System[T]` marks fields managed by your system (like auto-generated IDs). These fields are excluded from BuildDTOs but required in ViewDTOs, maintaining clear boundaries between user input and system-managed data.

**Key concepts:** Auto-generated values, security, explicit contracts

### [Separation of Concerns](separation-of-concerns.md)

Potato enforces clean architecture with clear boundaries between presentation, domain, and infrastructure layers. Each layer has a well-defined responsibility, making your codebase maintainable and testable.

**Key concepts:** Layered architecture, dependency direction, testability

## How These Principles Work Together

These principles form a cohesive system:

1. **Domain-Driven Design** provides the foundation for modeling your business
2. **Data Transfer Objects** enable clean boundaries between layers
3. **Unidirectional Data Flow** ensures predictable data transformations
4. **Type Safety** catches errors early in the development process
5. **Immutability** prevents accidental mutations in output data
6. **System Fields** separate user input from system-managed data
7. **Separation of Concerns** organizes code into maintainable layers

## Quick Start

**New to Potato?** Start with these philosophy guides in order:

1. [Domain-Driven Design](domain-driven-design.md) - Understand the foundation
2. [Data Transfer Objects](data-transfer-objects.md) - Learn about DTOs
3. [Unidirectional Data Flow](unidirectional-data-flow.md) - See how data flows

Then explore the remaining principles based on your interests.

## Next Steps

- **Ready to code?** Check out the [Quickstart Guide](../quickstart.md)
- **Want implementation details?** Explore the [Core Features](../core/domain.md)
- **Looking for examples?** See [Real-World Examples](../guides/examples.md)
