class ScreenerError(Exception):
    """Base exception for the Value Investing Screener."""
    pass

class DataProviderError(ScreenerError):
    """Raised when a data provider (SEC/Market) fails."""
    pass

class SECDataError(DataProviderError):
    """Raised when SEC data is missing or malformed."""
    pass

class MarketDataError(DataProviderError):
    """Raised when market data is unavailable or inconsistent."""
    pass

class ValuationError(ScreenerError):
    """Raised when a valuation model fails to calculate values."""
    pass
