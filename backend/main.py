"""
backend/main.py
FastAPI application entry point.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.database import connect_to_mongo, close_mongo_connection
from backend.routes import claims, policy, employees, audit


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    await connect_to_mongo()
    yield
    await close_mongo_connection()


app = FastAPI(
    title="Expenso API",
    description="Policy-First Expense Auditor with Explainable AI",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
        "http://localhost:3000",
        "https://expenso-frontend-*.run.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────
app.include_router(claims.router)
app.include_router(policy.router)
app.include_router(employees.router)
app.include_router(audit.router)


# ── Health check (required for GCP Cloud Run) ────────────
@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/")
async def root():
    return {"message": "Expenso API", "docs": "/docs"}
