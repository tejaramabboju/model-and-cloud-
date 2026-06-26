"""
FastAPI application entry point.
Sets up lifespan, CORS, and route registration.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import use_cases, dashboard, feedback, chat

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — initialize DB on startup."""
    logger.info("Starting AI Model & Cloud Advisor API...")
    init_db()
    logger.info("Database tables created / verified.")
    yield
    logger.info("Shutting down AI Model & Cloud Advisor API.")


app = FastAPI(
    title="AI Model & Cloud Advisor API",
    description=(
        "An intelligent advisor that recommends the best AI model and cloud "
        "provider configuration based on your use case requirements."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS Middleware ──────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register Routers ────────────────────────────────────────────────────────
app.include_router(use_cases.router)
app.include_router(dashboard.router)
app.include_router(feedback.router)
app.include_router(chat.router)


# ── Root Endpoint ────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    """Health check / root endpoint."""
    return {"message": "AI Model & Cloud Advisor API"}
