from pydantic import BaseModel, Field
from typing import List, Optional


class SuperinvestorProfile(BaseModel):
    """Curated value investing superinvestor metadata."""
    cik: str = Field(..., description="10-digit SEC CIK")
    manager: str = Field(..., description="Lead portfolio manager")
    fund_name: str = Field(..., description="Institutional investment manager name")
    style: str = Field(..., description="Investment philosophy")
    note: Optional[str] = Field(default=None, description="Additional notes (e.g. non-US holdings)")


class SuperinvestorHolding(BaseModel):
    """Single 13F-HR equity position."""
    cusip: str = Field(default="", description="CUSIP identifier")
    ticker: Optional[str] = Field(default=None, description="Resolved ticker symbol if available")
    issuer: str = Field(..., description="Company / Issuer name")
    shares: float = Field(default=0.0, description="Share count")
    value_usd: float = Field(default=0.0, description="Market value in USD")
    weight_pct: float = Field(default=0.0, description="Portfolio allocation %")
    activity: str = Field(default="HELD", description="QoQ activity: NEW, ADDED, REDUCED, UNCHANGED, HELD")
    share_change_pct: Optional[float] = Field(default=None, description="QoQ share count % change")


class SuperinvestorPortfolioResponse(BaseModel):
    """Latest 13F-HR portfolio holdings for a superinvestor."""
    cik: str
    manager: str
    fund_name: str
    style: str
    filing_date: str = ""
    report_period: str = ""
    previous_report_period: Optional[str] = None
    total_value_usd: float = 0.0
    holdings_count: int = 0
    sec_url: str = ""
    holdings: List[SuperinvestorHolding] = Field(default_factory=list)
    source: str = "SEC EDGAR 13F-HR"
