"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import init_db
from presentation.routers import users, posts, comments


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan handler.
    
    Initializes database on startup.
    """
    # Startup: Initialize database
    init_db()
    print("✅ Database initialized")
    
    yield
    
    # Shutdown: cleanup if needed
    print("👋 Shutting down")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    **Potato Example Application** - A Blog Management System demonstrating the potato package.
    
    ## Features Demonstrated
    
    ### Potato Package Features
    - **ViewDTO**: Outbound data transformation with field mapping and computed fields
    - **BuildDTO**: Inbound data validation with System field exclusion
    - **Aggregates**: Multi-domain composition (Post+User, Comment+User+Post)
    - **System Fields**: Auto-generated IDs and timestamps
    - **Field Mapping**: Renaming fields (username → login)
    - **Computed Fields**: Derived data (@computed decorator)
    
    ### Architecture
    - **DDD Layers**: Domain → Infrastructure → Application → Presentation
    - **Repository Pattern**: Abstract interfaces with concrete implementations
    - **Dependency Injection**: Clean service dependencies
    - **SQLAlchemy ORM**: Modern SQLAlchemy 2.0 with SQLite
    
    ## Endpoints
    - **Users**: Create, read, update, delete users
    - **Posts**: Manage blog posts with author information
    - **Comments**: Comments on posts with full context
    """,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router, prefix=settings.api_prefix)
app.include_router(posts.router, prefix=settings.api_prefix)
app.include_router(comments.router, prefix=settings.api_prefix)


@app.get("/")
def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "message": "Potato Example - Blog Management System",
        "docs": "/docs",
        "openapi": "/openapi.json",
    }


@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}
