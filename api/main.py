"""FastAPI application factory."""

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from api.database import Base, engine
from api.models import *  # noqa: F401, F403 — register all ORM models with Base
from api.routers import analyze, auth, carriers, datasets, reports, runs, tools

# Origins allowed for CORS (dev: Vite dev server; prod: frontend URL)
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("FRONTEND_URL", "http://localhost:5173").split(",")
]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Create DB tables on startup (no-op if already exist)."""
    Path("data/datasets").mkdir(parents=True, exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Add notes column to existing DBs that predate this field
        try:
            await conn.execute(text("ALTER TABLE analysis_runs ADD COLUMN notes TEXT"))
        except Exception:
            pass  # Column already exists
        try:
            await conn.execute(text("ALTER TABLE analysis_runs ADD COLUMN orders_validation_result JSON"))
        except Exception:
            pass  # Column already exists
        try:
            await conn.execute(text("ALTER TABLE analysis_runs ADD COLUMN masterdata_original_filename TEXT"))
        except Exception:
            pass  # Column already exists
        try:
            await conn.execute(text("ALTER TABLE analysis_runs ADD COLUMN orders_original_filename TEXT"))
        except Exception:
            pass  # Column already exists
        try:
            await conn.execute(text("ALTER TABLE datasets ADD COLUMN notes TEXT"))
        except Exception:
            pass  # Column already exists
        # Migration: datasets.file_hash had unique=True in schema v1 — drop and recreate
        # (table is new with no production data, safe to recreate)
        try:
            await conn.execute(text(
                "INSERT INTO datasets (id, name, file_type, row_count, duckdb_path, file_hash, created_at) "
                "VALUES ('_mig_a', '_', 'masterdata', 0, '_', '_mig_hash', CURRENT_TIMESTAMP),"
                "       ('_mig_b', '_', 'masterdata', 0, '_', '_mig_hash', CURRENT_TIMESTAMP)"
            ))
            await conn.execute(text("DELETE FROM datasets WHERE id IN ('_mig_a', '_mig_b')"))
        except Exception:
            # Unique constraint still present — recreate the table
            await conn.execute(text("DROP TABLE IF EXISTS datasets"))
            await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="Datavisor API",
    description="Warehouse analytics API — capacity, quality, performance",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze.router)
app.include_router(auth.router)
app.include_router(runs.router)
app.include_router(carriers.router)
app.include_router(reports.router)
app.include_router(datasets.router)
app.include_router(tools.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
