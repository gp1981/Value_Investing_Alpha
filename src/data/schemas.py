from dataclasses import dataclass
from typing import Optional, Dict

@dataclass(frozen=True)
class FinancialStatement:
    """Unified schema for fundamental data sourced from SEC filings."""
    ticker: str
    ebit: float
    total_assets: float
    total_liabilities: float
    current_assets: float
    current_liabilities: float
    cash_and_equivalents: float
    short_term_debt: float
    long_term_debt: float
    net_fixed_assets: float
    shares_outstanding: int
    company_name: Optional[str] = "N/A"
    description: Optional[str] = "N/A"
    sic_code: Optional[int] = None
    industry: Optional[str] = None
    accounts_receivable: Optional[float] = 0.0
    inventory: Optional[float] = 0.0
    revenue: Optional[float] = 0.0
    operating_income: Optional[float] = 0.0
    net_income: Optional[float] = 0.0
    depreciation_amortization: Optional[float] = 0.0
    capex: Optional[float] = 0.0
    goodwill_and_intangible_assets: Optional[float] = 0.0
    shareholders_equity: Optional[float] = 0.0
    accounts_payable: Optional[float] = 0.0
    interest_expense_ttm: Optional[float] = 0.0
    income_tax_expense_ttm: Optional[float] = 0.0
    operating_cash_flow: Optional[float] = 0.0
    free_cash_flow: Optional[float] = 0.0
    revenue_history: Optional[Dict[str, float]] = None  # Keyed by date or period label
    prev_revenue: Optional[float] = 0.0
    prev_accounts_receivable: Optional[float] = 0.0
    prev_inventory: Optional[float] = 0.0
    wc_anomaly_signal: Optional[str] = "N/A"
    ar_divergence: Optional[float] = 0.0
    inv_divergence: Optional[float] = 0.0

@dataclass(frozen=True)
class MarketData:
    """Schema for market-specific data sourced from providers like yfinance."""
    ticker: str
    price: float
    market_cap: float
    shares_outstanding: int
    last_updated: str

@dataclass(frozen=True)
class ValuationResult:
    """Standardized output for valuation model results."""
    ticker: str
    model_name: str
    intrinsic_value: float
    current_price: float
    margin_of_safety: float
    metrics: Dict[str, float]
