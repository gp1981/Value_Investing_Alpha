"""
FastAPI application entrypoint for Value Investing Alpha.
Provides REST endpoints and terminal streaming for financial metrics,
fundamental data (SEC Edgar), and market data (yfinance).
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

# Register routes
app.include_router(health.router)
app.include_router(screener.router)
app.include_router(company.router)

@app.get("/")
def root():
    return {
        "message": "Welcome to Value Investing Alpha API",
        "docs_url": "/docs",
        "status": "operational"
    }
