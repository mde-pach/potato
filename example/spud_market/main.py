"""Spud Market — a farm-to-table marketplace built with Potato + FastAPI."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from example.spud_market.database import init_db
from example.spud_market.presentation.routers import (
    farmer_router,
    order_router,
    product_router,
)
from example.spud_market.seed import seed_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_data()
    yield


app = FastAPI(
    title="Spud Market",
    version="0.1.0",
    description="A farm-to-table marketplace — tutorial example for Potato.",
    lifespan=lifespan,
)

app.include_router(product_router, prefix="/api")
app.include_router(farmer_router, prefix="/api")
app.include_router(order_router, prefix="/api")


@app.get("/")
def root():
    return {"app": "Spud Market", "docs": "/docs"}
