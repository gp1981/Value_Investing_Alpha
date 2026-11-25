import os
from functools import lru_cache
from src.data.sec_provider import SECProvider
from src.data.market_provider import MarketDataProvider
from src.engine.integrator import DataIntegrator
from src.engine.screener import Screener
from src.utils.storage import resolve_edgar_paths, DEFAULT_OUTPUT_DIR

@lru_cache()
def get_sec_provider() -> SECProvider:
    """Dependency for SEC data provider with graceful local fallback."""
    identity = os.getenv("EDGAR_IDENTITY", "Value Investing Alpha alpha@example.com")
    data_dir, _, _ = resolve_edgar_paths()
    return SECProvider(identity=identity, storage_dir=data_dir)

@lru_cache()
def get_market_provider() -> MarketDataProvider:
    """Dependency for market data provider."""
    return MarketDataProvider()

def get_integrator() -> DataIntegrator:
    """Dependency for integrated SEC + Market data."""
    return DataIntegrator(get_sec_provider(), get_market_provider())

def get_screener() -> Screener:
    """Dependency for screener orchestrator."""
    return Screener(get_integrator(), output_dir="output")
