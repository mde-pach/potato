# Tutorial: Building Spud Market

Welcome to the Potato tutorial. Over 6 steps, you'll build **Spud Market** — a working farm-to-table marketplace API with FastAPI, SQLAlchemy, and Potato handling all the data transformations.

This isn't a concept demo. By the end, you'll have a real application with a database, seeded data, CRUD endpoints, and every Potato feature wired into production-like code.

## What you'll build

Spud Market is an online platform where local farmers list produce and customers place orders. The API supports:

- Browsing products (with farmer info)
- Full product CRUD
- Farmer profiles with access control
- Orders with line items and computed totals

## The steps

| Step | What you'll build | Concepts introduced |
|------|-------------------|---------------------|
| [1. Domain & Database](step-01-domain-and-database.md) | Domain models + SQLAlchemy persistence | `Domain`, `Auto[T]`, `Private[T]` |
| [2. The Product API](step-02-product-api.md) | Product CRUD with views and forms | `ViewDTO`, `BuildDTO`, `@computed`, `Field(transform=...)`, inheritance, `partial`, `apply_to()` |
| [3. The Farmer API](step-03-farmer-api.md) | Farmer profiles with data protection | `Field(source=...)`, deep flattening, `Private` enforcement |
| [4. The Order API](step-04-order-api.md) | Multi-domain orders with line items | `Aggregate`, nested ViewDTOs, `@before_build`, `@after_build` |
| [5. Access Control & Errors](step-05-access-control-and-errors.md) | Context-based visibility + error safety net | `Field(visible=...)`, context, error messages |
| [6. The Complete Spud Market](step-06-complete.md) | Running the full application | Full code reference, how to run, recap |

## Prerequisites

- Python 3.12+
- Familiarity with Pydantic and FastAPI basics

## Project structure

The finished application lives in `example/spud_market/` and follows a clean architecture layout:

```
example/spud_market/
├── main.py                        # FastAPI application
├── database.py                    # SQLAlchemy engine and session
├── seed.py                        # Sample data
├── domain/
│   ├── models.py                  # Potato domain models
│   └── aggregates.py              # Multi-domain aggregates
├── infrastructure/
│   ├── db_models.py               # SQLAlchemy ORM models
│   ├── mappers.py                 # Domain ↔ database mapping
│   └── repositories.py            # Data access
├── application/
│   ├── dtos.py                    # Potato ViewDTOs and BuildDTOs
│   ├── context.py                 # Permissions context
│   └── services.py                # Business logic
└── presentation/
    └── routers.py                 # FastAPI routes
```

Each tutorial step references the actual code in this directory. You can follow along by reading the files, or run the finished app directly.

[Start with Step 1: Domain & Database :material-arrow-right:](step-01-domain-and-database.md){ .md-button .md-button--primary }
