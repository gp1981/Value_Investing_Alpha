import os
from functools import lru_cache
from src.data.sec_provider import SECProvider
from src.data.market_provider import MarketDataProvider
from src.engine.integrator import DataIntegrator
from src.engine.screener import Screener

@lru_cache()
def get_sec_provider() -> SECProvider:
    """Dependency for SEC data provider."""
    identity = os.getenv("EDGAR_IDENTITY", "Value Investing Alpha alpha@example.com")
    storage_dir = os.getenv("EDGAR_LOCAL_DATA_DIR", "output")
    return SECProvider(identity=identity, storage_dir=storage_dir)

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
