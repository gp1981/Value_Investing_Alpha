from ..data.sec_provider import SECProvider
from ..data.market_provider import MarketDataProvider
from ..data.schemas import FinancialStatement, MarketData
from ..data.exceptions import DataProviderError
import logging

class DataIntegrator:
    """Coordinates data retrieval from SEC and Market providers."""
    
    def __init__(self, sec_provider: SECProvider, market_provider: MarketDataProvider):
        self.sec = sec_provider
        self.market = market_provider
        self.logger = logging.getLogger(__name__)

    def fetch_company_data(self, ticker: str, enrich: bool = False):
        """Fetch and integrate data for a single company."""
        try:
            # Fetch fundamentals from SEC
            fs = self.sec.get_financials(ticker, enrich=enrich)
            
            # Fetch market data from yfinance
            md = self.market.get_market_data(ticker)
            
            # Consistency Check: Shares Outstanding
            # If SEC and Market data differ by > 5%, log a warning and use SEC data
            if fs and fs.shares_outstanding and fs.shares_outstanding > 0:
                diff = abs(fs.shares_outstanding - md.shares_outstanding) / fs.shares_outstanding
                if diff > 0.05:
                    self.logger.warning(
                        f"Significant discrepancy in shares outstanding for {ticker}: "
                        f"SEC={fs.shares_outstanding}, Market={md.shares_outstanding}. "
                        "Defaulting to SEC data."
                    )
            
            return fs, md
            
        except Exception as e:
            raise DataProviderError(f"Error integrating data for {ticker}: {str(e)}")

    def fetch_historical_data(self, ticker: str, max_years: int = 20):
        """Fetch historical fundamental data for equity analysis."""
        return self.sec.get_historical_data(ticker, max_years=max_years)
            
    def get_discount_rate(self) -> float:
        """Get the discount rate based on S&P 500 annualized return."""
        return self.market.get_sp500_annualized_return(years=10)
