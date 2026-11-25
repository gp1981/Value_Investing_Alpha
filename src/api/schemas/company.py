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

class StatementRow(BaseModel):
    """Line item in a multi-period structured financial statement."""
    concept: str = Field(..., description="US-GAAP concept identifier")
    label: str = Field(..., description="Human-readable financial statement label")
    depth: int = Field(default=0, description="Hierarchy indentation depth level")
    is_abstract: bool = Field(default=False, description="Whether line is a section header")
    is_total: bool = Field(default=False, description="Whether line is a subtotal or grand total")
    values: Dict[str, Optional[float]] = Field(default_factory=dict, description="Values mapped per fiscal period column (e.g. FY 2026)")

class StatementReport(BaseModel):
    """Full statement report containing period header columns and rows."""
    periods: List[str] = Field(default_factory=list, description="Fiscal period columns (e.g. ['FY 2026', 'FY 2025'])")
    rows: List[StatementRow] = Field(default_factory=list, description="Ordered statement line items")

class CompanyStatementsResponse(BaseModel):
    """Complete multi-period financial statements (BS, IS, CF)."""
    ticker: str = Field(..., description="Ticker symbol")
    company_name: str = Field(..., description="Reporting entity name")
    balance_sheet: Optional[StatementReport] = Field(default=None, description="Multi-period Balance Sheet")
    income_statement: Optional[StatementReport] = Field(default=None, description="Multi-period Income Statement")
    cash_flow: Optional[StatementReport] = Field(default=None, description="Multi-period Statement of Cash Flows")

class FilingSectionItem(BaseModel):
    """Section bookmark with identifier and human-readable description."""
    id: str = Field(..., description="Section identifier (e.g. 'Item 1')")
    title: str = Field(..., description="Full descriptive label (e.g. 'Item 1 - Business')")

class FilingAttachmentItem(BaseModel):
    """Official SEC filing attachment / exhibit link."""
    document: str = Field(..., description="Filename of the attachment")
    description: str = Field(default="", description="Attachment description")
    doc_type: str = Field(default="", description="Exhibit or document type (e.g. EX-10.1)")
    url: str = Field(..., description="Direct SEC EDGAR URL")

class FilingContentResponse(BaseModel):
    """Structured text content, sections, and attachments of a regulatory SEC filing."""
    ticker: str = Field(..., description="Ticker symbol")
    accession_number: str = Field(..., description="SEC accession identifier")
    form: str = Field(..., description="Filing type (e.g. 10-K, 10-Q, 8-K, 13F-HR)")
    filing_date: str = Field(..., description="Filing date")
    report_date: Optional[str] = Field(default=None, description="Report date")
    available_sections: List[str] = Field(default_factory=list, description="List of recognized section IDs")
    section_bookmarks: List[FilingSectionItem] = Field(default_factory=list, description="Descriptive section bookmarks")
    attachments: List[FilingAttachmentItem] = Field(default_factory=list, description="Exhibits and attachments")
    selected_section: Optional[str] = Field(default=None, description="Currently displayed section/item")
    content: str = Field(..., description="Extracted clean markdown/text content of the selected section or document")
    sec_url: str = Field(..., description="Official SEC EDGAR index URL")

class FilingDiffRequest(BaseModel):
    """Request payload to compute redline word diff between two filings."""
    form: str = Field(default="10-K", description="Filing form type")
    accession_1: str = Field(..., description="Accession number of first filing (e.g. newer year)")
    accession_2: str = Field(..., description="Accession number of second filing (e.g. prior year)")
    section: str = Field(default="Item 1", description="Section/Item name to compare (e.g. 'Item 1', 'Item 1A', 'Item 7')")

class DiffToken(BaseModel):
    """Word or phrase diff token."""
    type: str = Field(..., description="Diff status: 'equal', 'added', or 'removed'")
    text: str = Field(..., description="Text segment")

class FilingDiffResponse(BaseModel):
    """Detailed word-level redline comparison between two SEC filings."""
    ticker: str = Field(..., description="Ticker symbol")
    form: str = Field(..., description="Filing form type")
    section: str = Field(..., description="Compared section")
    accession_1: str = Field(..., description="Newer filing accession")
    accession_2: str = Field(..., description="Prior filing accession")
    date_1: str = Field(default="", description="Filing date 1")
    date_2: str = Field(default="", description="Filing date 2")
    similarity_pct: float = Field(..., description="Overall text similarity percentage (0-100%)")
    words_added: int = Field(..., description="Count of newly added words")
    words_removed: int = Field(..., description="Count of deleted/modified words")
    tokens: List[DiffToken] = Field(default_factory=list, description="Inline token stream with equal/added/removed tags")


class InsiderTransactionItem(BaseModel):
    """Form 4 insider transaction."""
    filing_date: str
    transaction_date: str = ""
    insider_name: str
    title: str = ""
    transaction_code: str = Field(..., description="P=Purchase, S=Sale, M=Exercise, etc.")
    shares: float = 0.0
    price: Optional[float] = None
    value_usd: Optional[float] = None
    sec_url: str = ""


class InsiderRadarResponse(BaseModel):
    """Form 4 insider trading summary with 30-day Cluster Buying detection."""
    ticker: str
    cluster_buying_detected: bool = False
    cluster_buyers_count: int = 0
    total_purchases_usd: float = 0.0
    total_sales_usd: float = 0.0
    transactions: List[InsiderTransactionItem] = Field(default_factory=list)


class MaterialEventItem(BaseModel):
    """Form 8-K material corporate event."""
    filing_date: str
    accession_number: str
    items: List[str] = Field(default_factory=list)
    summary: str = ""
    sec_url: str = ""


class MaterialEventsResponse(BaseModel):
    """Recent Form 8-K material events for a company."""
    ticker: str
    events: List[MaterialEventItem] = Field(default_factory=list)


class GovernanceResponse(BaseModel):
    """DEF 14A proxy statement & executive alignment summary."""
    ticker: str
    filing_date: str = ""
    accession_number: str = ""
    sec_url: str = ""
    summary: str = ""
    compensation_rows: List[Dict[str, Any]] = Field(default_factory=list)


class FilingSearchRequest(BaseModel):
    """Full-text keyword search request within a filing."""
    query: str = Field(..., min_length=2)
    form: str = Field(default="10-K")
    accession_number: Optional[str] = None


class FilingSearchHit(BaseModel):
    """Matching snippet from filing full-text search."""
    section: str
    snippet: str


class FilingSearchResponse(BaseModel):
    """Full-text search results across a company's SEC filing."""
    ticker: str
    form: str
    filing_date: str
    accession_number: str
    query: str
    total_hits: int
    hits: List[FilingSearchHit] = Field(default_factory=list)
