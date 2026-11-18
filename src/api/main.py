"""
FastAPI application entrypoint for Value Investing Alpha.
Provides REST endpoints and terminal streaming for financial metrics,
fundamental data (SEC Edgar), and market data (yfinance).
"""

import os
# Set default local storage to avoid ~/.edgar and SSD exhaustion
_default_data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../output/data"))
_default_cache_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../output/cache"))
os.makedirs(_default_data_dir, exist_ok=True)
os.makedirs(_default_cache_dir, exist_ok=True)
os.environ.setdefault("EDGAR_LOCAL_DATA_DIR", _default_data_dir)
os.environ.setdefault("EDGAR_CACHE_DIR", _default_cache_dir)
os.environ.setdefault("EDGAR_IDENTITY", "Value Investing Alpha alpha@example.com")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from src.api.routes import health, screener, company

app = FastAPI(
    title="Value Investing Alpha API",
    description="High-integrity value investing screener and terminal API (Magic Formula, EPV, Reproduction Cost, DCF)",
    version="1.0.0"
)

# Enable CORS for local web development and terminal frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(health.router)
app.include_router(screener.router)
app.include_router(company.router)

# Mount static frontend build if present (for single-container serverless deployment)
frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/dist"))
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")


@app.get("/")
def root():
    return {
        "message": "Welcome to Value Investing Alpha API",
        "docs_url": "/docs",
        "status": "operational"
    }
