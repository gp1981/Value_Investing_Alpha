from typing import List, Optional
from pydantic import BaseModel, Field

class ScreenerRunRequest(BaseModel):
    """Parameters for executing a stock screen."""
    tickers: Optional[List[str]] = Field(
        default=None,
        description="Optional explicit list of tickers to screen (e.g., ['AAPL', 'MSFT', 'GOOGL'])"
    )
    min_market_cap: float = Field(
        default=50_000_000.0,
        description="Minimum market capitalization in USD"
    )
    max_market_cap: Optional[float] = Field(
        default=None,
        description="Maximum market capitalization in USD"
    )
    exclude_financials: bool = Field(
        default=True,
        description="Exclude banks and insurance institutions (SIC 6000-6999)"
    )
    exclude_foreign: bool = Field(
        default=True,
        description="Exclude foreign companies and ADRs"
    )
    sort_by: str = Field(
        default="magic_formula_rank",
        description="Field to sort by: magic_formula_rank, earnings_yield, return_on_capital, epv_margin_of_safety, market_cap"
    )
    sort_order: str = Field(
        default="asc",
        description="Sort direction: asc or desc"
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=500,
        description="Maximum number of ranked results to return"
    )

class ScreenerStockItem(BaseModel):
    """Individual ranked company in screener results."""
    rank: int = Field(..., description="Screen ranking position")
    ticker: str = Field(..., description="Stock ticker symbol")
    company_name: str = Field(..., description="Company reporting name")
    sector: Optional[str] = Field(default="N/A", description="Industry or sector name")
    sic_code: Optional[int] = Field(default=None, description="Standard Industrial Classification code")
    price: float = Field(..., description="Current stock market price")
    market_cap: float = Field(..., description="Market capitalization")
    enterprise_value: float = Field(..., description="Enterprise Value")
    ebit: float = Field(..., description="Trailing Twelve Month EBIT")
    earnings_yield: float = Field(..., description="EBIT / Enterprise Value")
    return_on_capital: float = Field(..., description="EBIT / Tangible Capital Employed")
    magic_formula_rank: Optional[int] = Field(default=None, description="Combined Magic Formula rank")
    reproduction_value_per_share: Optional[float] = Field(default=None, description="Net reproduction asset value per share")
    epv_per_share: Optional[float] = Field(default=None, description="Earning power value per share")
    epv_margin_of_safety: Optional[float] = Field(default=None, description="Margin of safety based on EPV vs price")
    traffic_light: Optional[str] = Field(default="YELLOW", description="Solvency & safety rating: GREEN, YELLOW, RED")
    wc_anomaly: Optional[str] = Field(default="NORMAL", description="Working capital divergence flag")
    fcff_ttm: Optional[float] = Field(default=None, description="Free Cash Flow to Firm (TTM)")
    mc_to_fcff_ttm: Optional[float] = Field(default=None, description="Market Cap / FCFF TTM (payback years)")
    mc_to_fcff_5y_avg: Optional[float] = Field(default=None, description="Market Cap / 5Y Avg FCFF (payback years)")

class ScreenerResultsResponse(BaseModel):
    """Container response for screener output."""
    total_count: int = Field(..., description="Total companies matching filters")
    returned_count: int = Field(..., description="Number of results in this response")
    source: str = Field(..., description="Data origin: 'cache' or 'live'")
    timestamp: str = Field(..., description="ISO 8601 timestamp of analysis")
    items: List[ScreenerStockItem] = Field(..., description="Ranked list of companies")
