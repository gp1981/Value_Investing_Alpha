from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

class SECFilingItem(BaseModel):
    """Metadata and direct SEC links for an individual regulatory filing."""
    form: str = Field(..., description="Filing type (e.g. 10-K, 10-Q, 8-K)")
    filing_date: str = Field(..., description="Date filed with SEC (YYYY-MM-DD)")
    report_date: Optional[str] = Field(default=None, description="Period of report date")
    accession_number: str = Field(..., description="Unique SEC accession number")
    description: Optional[str] = Field(default="", description="Filing or primary document description")
    url: str = Field(..., description="Official SEC EDGAR index URL")
    interactive_url: Optional[str] = Field(default=None, description="Interactive XBRL Data viewer URL if available")

class MagicFormulaDetails(BaseModel):
    """Detailed breakdown of Greenblatt's Magic Formula calculation."""
    ebit: float = Field(..., description="Operating earnings (EBIT)")
    enterprise_value: float = Field(..., description="Enterprise Value (EV = Market Cap + Debt - Excess Cash)")
    earnings_yield: float = Field(..., description="EBIT / Enterprise Value")
    tangible_capital_employed: float = Field(..., description="Tangible Capital = Total Assets - Intangibles - Cash")
    return_on_capital: float = Field(..., description="EBIT / Tangible Capital Employed")
    excess_cash: float = Field(default=0.0, description="Estimated excess cash above operational needs")

class GreenwaldDetails(BaseModel):
    """Detailed Bruce Greenwald Asset Reproduction & EPV breakdown."""
    reproduction_value: float = Field(..., description="Asset Reproduction Cost of firm")
    reproduction_value_per_share: float = Field(..., description="Reproduction Cost per share")
    epv: float = Field(..., description="Total Earning Power Value")
    epv_per_share: float = Field(..., description="EPV equity value per share")
    wacc: float = Field(default=0.10, description="Cost of Capital discount rate")
    tax_rate: float = Field(default=0.25, description="Normalized tax rate")
    franchise_factor: float = Field(
        ...,
        description="Ratio of EPV to Reproduction Value. Value > 1.0 indicates structural competitive moat"
    )
    margin_of_safety: float = Field(..., description="Discount / premium of current price to EPV per share")

class DCFDetails(BaseModel):
    """Steady-state Discounted Cash Flow valuation."""
    intrinsic_value: float = Field(..., description="Firm intrinsic value via DCF")
    intrinsic_value_per_share: float = Field(..., description="Intrinsic value per share")
    discount_rate: float = Field(..., description="Annualized discount hurdle rate")
    growth_rate: float = Field(default=0.02, description="Perpetual growth rate")
    margin_of_safety: float = Field(..., description="Percentage discount to intrinsic value")

class SafetyDetails(BaseModel):
    """Financial solvency and earnings quality signals."""
    traffic_light: str = Field(..., description="GREEN, YELLOW, or RED safety rating")
    quick_ratio: float = Field(..., description="Quick Ratio = (Current Assets - Inventory) / Current Liabilities")
    debt_to_equity: float = Field(..., description="Total Debt / Shareholders' Equity")
    debt_to_assets: float = Field(..., description="Total Debt / Total Assets")
    revenue_zscore_label: str = Field(..., description="Outlier label: High, Normal, Low, or N/A")
    wc_anomaly_signal: str = Field(..., description="Working capital divergence flag")

class CompanyDetailResponse(BaseModel):
    """Unified comprehensive financial profile for a ticker."""
    ticker: str = Field(..., description="Ticker symbol")
    company_name: str = Field(..., description="Official reporting entity name")
    description: Optional[str] = Field(default="N/A", description="Business profile")
    sic_code: Optional[int] = Field(default=None, description="SIC classification")
    industry: Optional[str] = Field(default="N/A", description="Industry classification")
    price: float = Field(..., description="Current market share price")
    market_cap: float = Field(..., description="Current market capitalization")
    shares_outstanding: int = Field(..., description="Total diluted shares outstanding")
    magic_formula: MagicFormulaDetails
    greenwald: GreenwaldDetails
    dcf: DCFDetails
    safety: SafetyDetails
    financial_statement: Dict[str, Any] = Field(..., description="Raw XBRL line items extracted from SEC filings")
    filings: List[SECFilingItem] = Field(default_factory=list, description="Recent regulatory SEC filings (10-K, 10-Q, 8-K)")
