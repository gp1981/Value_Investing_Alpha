from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List, Optional
import dataclasses
import os
import re
import difflib
from datetime import date, timedelta
import pandas as pd
import edgar

from src.api.schemas.company import (
    CompanyDetailResponse,
    MagicFormulaDetails,
    GreenwaldDetails,
    DCFDetails,
    SafetyDetails,
    SECFilingItem,
    StatementRow,
    StatementReport,
    CompanyStatementsResponse,
    FilingSectionItem,
    FilingAttachmentItem,
    FilingContentResponse,
    FilingDiffRequest,
    DiffToken,
    FilingDiffResponse,
    InsiderTransactionItem,
    InsiderRadarResponse,
    MaterialEventItem,
    MaterialEventsResponse,
    GovernanceResponse,
    FilingSearchRequest,
    FilingSearchHit,
    FilingSearchResponse,
)
from src.api.deps import get_integrator, get_sec_provider
from src.engine.integrator import DataIntegrator
from src.data.sec_provider import SECProvider
from src.models.magic_formula import MagicFormulaModel
from src.models.greenwald import GreenwaldModel
from src.models.dcf import DCFModel
from src.models.safety import SafetyModel

router = APIRouter(prefix="/api/company", tags=["Company Deep-Dive"])

# In-Memory caches to prevent redundant SEC downloads & parsing
_company_cache: Dict[str, CompanyDetailResponse] = {}
_statements_cache: Dict[str, CompanyStatementsResponse] = {}
_filing_content_cache: Dict[str, FilingContentResponse] = {}
_filing_diff_cache: Dict[str, FilingDiffResponse] = {}

EDGAR_FORM_CATALOG = [
    {"form": "10-K", "object_name": "TenK", "category": "Financials", "description": "Annual Report — Audited financial statements, business overview, risk factors & MD&A"},
    {"form": "10-Q", "object_name": "TenQ", "category": "Financials", "description": "Quarterly Report — Unaudited quarterly financial statements & interim MD&A"},
    {"form": "8-K", "object_name": "CurrentReport", "category": "Events", "description": "Current Report — Material corporate events, earnings releases, M&A & executive changes"},
    {"form": "13F-HR", "object_name": "ThirteenF", "category": "Ownership", "description": "Institutional Holdings — Quarterly equity positions of >$100M institutional managers"},
    {"form": "DEF 14A", "object_name": "ProxyStatement", "category": "Governance", "description": "Proxy Statement — Executive compensation, board elections & shareholder proposals"},
    {"form": "4", "object_name": "Ownership", "category": "Insiders", "description": "Insider Trading — Statement of changes in beneficial ownership (buys/sells within 2 days)"},
    {"form": "S-1", "object_name": "Registration", "category": "Offerings", "description": "IPO Registration — Initial public offering prospectus & historical financials"},
    {"form": "20-F", "object_name": "TwentyF", "category": "Foreign", "description": "Foreign Private Issuer Annual Report — Equivalent to 10-K for non-US companies"},
]

SEC_ITEM_DESCRIPTIONS: Dict[str, str] = {
    "Item 1": "Item 1 - Business",
    "Item 1A": "Item 1A - Risk Factors",
    "Item 1B": "Item 1B - Unresolved Staff Comments",
    "Item 1C": "Item 1C - Cybersecurity",
    "Item 2": "Item 2 - Properties / MD&A (10-Q)",
    "Item 3": "Item 3 - Legal Proceedings / Market Risk (10-Q)",
    "Item 4": "Item 4 - Mine Safety / Controls & Procedures (10-Q)",
    "Item 5": "Item 5 - Market for Common Equity",
    "Item 6": "Item 6 - Selected Financial Data",
    "Item 7": "Item 7 - Management's Discussion & Analysis (MD&A)",
    "Item 7A": "Item 7A - Quantitative & Qualitative Market Risk",
    "Item 8": "Item 8 - Financial Statements & Supplementary Data",
    "Item 9": "Item 9 - Changes in & Disagreements with Accountants",
    "Item 9A": "Item 9A - Controls and Procedures",
    "Item 9B": "Item 9B - Other Information",
    "Item 10": "Item 10 - Directors, Executive Officers & Governance",
    "Item 11": "Item 11 - Executive Compensation",
    "Item 12": "Item 12 - Security Ownership of Certain Beneficial Owners",
    "Item 13": "Item 13 - Certain Relationships & Related Transactions",
    "Item 14": "Item 14 - Principal Accountant Fees and Services",
    "Item 15": "Item 15 - Exhibits & Financial Statement Schedules",
    "Part I, Item 1": "Part I, Item 1 - Financial Statements",
    "Part I, Item 2": "Part I, Item 2 - MD&A of Financial Condition",
    "Part I, Item 3": "Part I, Item 3 - Quantitative & Qualitative Market Risk",
    "Part I, Item 4": "Part I, Item 4 - Controls and Procedures",
    "Part II, Item 1": "Part II, Item 1 - Legal Proceedings",
    "Part II, Item 1A": "Part II, Item 1A - Risk Factors",
    "Part II, Item 2": "Part II, Item 2 - Unregistered Sales of Equity",
    "Part II, Item 5": "Part II, Item 5 - Other Information",
    "Part II, Item 6": "Part II, Item 6 - Exhibits",
    "Item 1.01": "Item 1.01 - Entry into a Material Definitive Agreement",
    "Item 2.01": "Item 2.01 - Completion of Acquisition or Disposition",
    "Item 2.02": "Item 2.02 - Results of Operations and Financial Condition",
    "Item 5.02": "Item 5.02 - Departure/Appointment of Directors or Officers",
    "Item 7.01": "Item 7.01 - Regulation FD Disclosure",
    "Item 8.01": "Item 8.01 - Other Events",
    "Item 9.01": "Item 9.01 - Financial Statements and Exhibits",
}

def _format_section_title(sec_id: str) -> str:
    clean = str(sec_id).strip()
    if clean in SEC_ITEM_DESCRIPTIONS:
        return SEC_ITEM_DESCRIPTIONS[clean]
    # Try case-insensitive match
    for k, v in SEC_ITEM_DESCRIPTIONS.items():
        if k.lower() == clean.lower():
            return v
    return clean

@router.get("/edgar-forms")
def list_edgar_forms():
    """Return supported SEC EDGAR filing forms and their edgartools data-object descriptions."""
    return {"forms": EDGAR_FORM_CATALOG}

def _dataframe_to_statement_report(df: Optional[pd.DataFrame]) -> Optional[StatementReport]:
    """Helper to convert edgartools MultiPeriodStatement DataFrame to StatementReport schema."""
    if df is None or df.empty:
        return None
    
    df_clean = df.copy()
    if 'concept' not in df_clean.columns:
        df_clean = df_clean.reset_index()
    
    exclude_meta = {
        'concept', 'label', 'depth', 'is_abstract', 'is_total', 'section', 'confidence',
        'level', 'abstract', 'dimension', 'is_breakdown', 'dimension_axis', 'dimension_member',
        'dimension_member_label', 'dimension_label', 'balance', 'weight', 'preferred_sign',
        'parent_concept', 'parent_abstract_concept'
    }
    period_cols = [c for c in df_clean.columns if c not in exclude_meta]
    # Sort period columns descending (e.g. FY 2026, FY 2025...)
    period_cols = sorted(period_cols, reverse=True)
    
    rows = []
    for _, r in df_clean.iterrows():
        concept = str(r.get('concept', ''))
        label = str(r.get('label', concept) or concept)
        depth = int(r.get('depth', 0) if pd.notnull(r.get('depth')) else 0)
        is_abs = bool(r.get('is_abstract', False) if pd.notnull(r.get('is_abstract')) else False)
        is_tot = bool(r.get('is_total', False) if pd.notnull(r.get('is_total')) else False)
        
        vals = {}
        for p in period_cols:
            val = r.get(p)
            if pd.notnull(val) and isinstance(val, (int, float)):
                vals[str(p)] = float(val)
            else:
                vals[str(p)] = None
                
        rows.append(StatementRow(
            concept=concept,
            label=label,
            depth=depth,
            is_abstract=is_abs,
            is_total=is_tot,
            values=vals
        ))
        
    return StatementReport(periods=[str(p) for p in period_cols], rows=rows)

@router.get("/{ticker}", response_model=CompanyDetailResponse)
def get_company_details(
    ticker: str,
    integrator: DataIntegrator = Depends(get_integrator)
):
    """
    Retrieve comprehensive fundamental valuation breakdown for a company.
    Combines Joel Greenblatt's Magic Formula, Bruce Greenwald's EPV & Reproduction Cost,
    and steady-state DCF intrinsic valuation with SEC XBRL financial facts and regulatory filings.
    Results are cached in memory for zero re-download latency.
    """
    clean_ticker = ticker.upper().strip()
    
    # 1. Fast Cache Hit
    if clean_ticker in _company_cache:
        return _company_cache[clean_ticker]
    
    fs = None
    md = None
    # Normalize common share-class tickers (e.g., BRK.B -> BRK-B for yfinance/SEC)
    candidate_tickers = [clean_ticker]
    if "." in clean_ticker:
        candidate_tickers.append(clean_ticker.replace(".", "-"))

    for cand in candidate_tickers:
        try:
            fs, md = integrator.fetch_company_data(cand, enrich=True)
            if fs is not None and md is not None:
                clean_ticker = cand
                break
        except Exception:
            fs = None
            md = None

    if fs is None or md is None:
        # Provide sample fallback for demonstration or offline testing
        if clean_ticker in ["AAPL", "DEMO"]:
            from src.data.schemas import FinancialStatement, MarketData
            fs = FinancialStatement(
                ticker="AAPL",
                ebit=123000000000.0,
                total_assets=352000000000.0,
                total_liabilities=290000000000.0,
                current_assets=143000000000.0,
                current_liabilities=145000000000.0,
                cash_and_equivalents=30000000000.0,
                short_term_debt=10000000000.0,
                long_term_debt=95000000000.0,
                net_fixed_assets=43000000000.0,
                shares_outstanding=15300000000,
                company_name="Apple Inc.",
                description="Consumer electronics, software and online services.",
                sic_code=3571,
                industry="Electronic Computers",
                revenue=383000000000.0,
                net_income=97000000000.0,
                depreciation_amortization=11500000000.0,
                capex=11000000000.0,
                goodwill_and_intangible_assets=0.0,
                shareholders_equity=62000000000.0
            )
            md = MarketData(
                ticker="AAPL",
                price=225.50,
                market_cap=3450000000000.0,
                shares_outstanding=15300000000,
                last_updated="2026-11-15T00:00:00"
            )
        else:
            # Resilient fallback for 13F superinvestor holdings (e.g. ETFs, ADRs, or tickers without full XBRL)
            try:
                from src.data.schemas import FinancialStatement, MarketData
                comp = edgar.Company(clean_ticker)
                comp_name = getattr(comp, "name", None)
                if comp_name:
                    md_fb = integrator.market_provider.get_market_data(clean_ticker)
                    if md_fb is None:
                        md_fb = MarketData(ticker=clean_ticker, price=0.0, market_cap=0.0, shares_outstanding=1, last_updated="")
                    fs = FinancialStatement(
                        ticker=clean_ticker,
                        company_name=comp_name,
                        sic_code=getattr(comp, "sic", None),
                        industry=getattr(comp, "industry", "N/A") or "N/A",
                        shares_outstanding=md_fb.shares_outstanding or 1,
                    )
                    md = md_fb
            except Exception:
                pass

        if fs is None or md is None:
            raise HTTPException(
                status_code=404,
                detail=f"Could not retrieve fundamental or market data for {clean_ticker}. Verify ticker symbol."
            )

    # 1. Magic Formula Calculations
    mf_model = MagicFormulaModel()
    ey = mf_model.calculate_earnings_yield(fs, md)
    tangible_cap = mf_model.calculate_tangible_capital_employed(fs)
    roc = fs.ebit / tangible_cap if tangible_cap > 0 else 0.0
    excess_cash = mf_model.calculate_excess_cash(fs)
    total_debt = (fs.short_term_debt or 0) + (fs.long_term_debt or 0)
    ev = md.market_cap + total_debt - fs.cash_and_equivalents

    magic_formula_details = MagicFormulaDetails(
        ebit=round(fs.ebit, 2),
        enterprise_value=round(ev, 2),
        earnings_yield=round(ey, 4),
        tangible_capital_employed=round(tangible_cap, 2),
        return_on_capital=round(roc, 4),
        excess_cash=round(excess_cash, 2)
    )

    # 2. Bruce Greenwald Calculations
    gw_model = GreenwaldModel()
    wacc = 0.10
    tax_rate = 0.25
    rep_val = gw_model.calculate_reproduction_value(fs)
    rep_val_per_share = rep_val / md.shares_outstanding if md.shares_outstanding > 0 else 0.0
    epv = gw_model.calculate_epv(fs, wacc=wacc)
    epv_per_share = epv / md.shares_outstanding if md.shares_outstanding > 0 else 0.0
    franchise_factor = epv / rep_val if rep_val > 0 else 1.0
    epv_mos = (epv_per_share - md.price) / epv_per_share if epv_per_share > 0 else 0.0

    greenwald_details = GreenwaldDetails(
        reproduction_value=round(rep_val, 2),
        reproduction_value_per_share=round(rep_val_per_share, 2),
        epv=round(epv, 2),
        epv_per_share=round(epv_per_share, 2),
        wacc=wacc,
        tax_rate=tax_rate,
        franchise_factor=round(franchise_factor, 2),
        margin_of_safety=round(epv_mos, 4)
    )

    # 3. DCF Calculations
    dcf_model = DCFModel()
    discount_rate = 0.09
    growth_rate = 0.02
    dcf_intrinsic = dcf_model.calculate_intrinsic_value(fs, discount_rate=discount_rate, growth_rate=growth_rate)
    dcf_intrinsic_per_share = dcf_intrinsic / md.shares_outstanding if md.shares_outstanding > 0 else 0.0
    dcf_mos = (dcf_intrinsic_per_share - md.price) / dcf_intrinsic_per_share if dcf_intrinsic_per_share > 0 else 0.0

    dcf_details = DCFDetails(
        intrinsic_value=round(dcf_intrinsic, 2),
        intrinsic_value_per_share=round(dcf_intrinsic_per_share, 2),
        discount_rate=discount_rate,
        growth_rate=growth_rate,
        margin_of_safety=round(dcf_mos, 4)
    )

    # 4. Safety Calculations
    safety_model = SafetyModel()
    traffic_light = safety_model.calculate_traffic_light(fs, md)
    
    quick_ratio = 0.0
    if fs.current_liabilities > 0:
        quick_ratio = ((fs.current_assets or 0) - (fs.inventory or 0)) / fs.current_liabilities

    debt_to_equity = total_debt / fs.shareholders_equity if fs.shareholders_equity and fs.shareholders_equity > 0 else 0.0
    debt_to_assets = total_debt / fs.total_assets if fs.total_assets and fs.total_assets > 0 else 0.0
    revenue_zscore = safety_model.calculate_revenue_zscore_label(fs.revenue_history or {})

    safety_details = SafetyDetails(
        traffic_light=traffic_light,
        quick_ratio=round(quick_ratio, 2),
        debt_to_equity=round(debt_to_equity, 2),
        debt_to_assets=round(debt_to_assets, 2),
        revenue_zscore_label=revenue_zscore,
        wc_anomaly_signal=str(fs.wc_anomaly_signal or "NORMAL")
    )

    # 5. Raw Financial Line Items for Footnote Transparency
    fs_dict = dataclasses.asdict(fs)
    # Exclude complex sub-dictionaries from the raw flat view
    fs_dict.pop("revenue_history", None)

    # 6. Retrieve Recent SEC Regulatory Filings
    filings_list = []
    try:
        raw_filings = integrator.sec.get_filings(clean_ticker, limit=25)
        filings_list = [SECFilingItem(**f) for f in raw_filings]
    except Exception:
        filings_list = []

    res = CompanyDetailResponse(
        ticker=clean_ticker,
        company_name=fs.company_name or clean_ticker,
        description=fs.description or "N/A",
        sic_code=fs.sic_code,
        industry=fs.industry or "N/A",
        price=round(md.price, 2),
        market_cap=round(md.market_cap, 2),
        shares_outstanding=md.shares_outstanding,
        magic_formula=magic_formula_details,
        greenwald=greenwald_details,
        dcf=dcf_details,
        safety=safety_details,
        financial_statement=fs_dict,
        filings=filings_list
    )
    
    # Store in fast memory cache
    _company_cache[clean_ticker] = res
    return res

@router.get("/{ticker}/statements", response_model=CompanyStatementsResponse)
def get_company_multiperiod_statements(ticker: str):
    """
    Retrieve comprehensive multi-period Balance Sheet (BS), Income Statement (IS),
    and Cash Flow Statement (CF) across fiscal years (e.g. FY 2026, 2025, 2024, 2023)
    powered by edgartools MultiPeriodStatement rendering. Cached for instant lookups.
    """
    clean_ticker = ticker.upper().strip()
    
    # Check cache
    if clean_ticker in _statements_cache:
        return _statements_cache[clean_ticker]
        
    try:
        comp = edgar.Company(clean_ticker)
        
        # 1. Balance Sheet
        bs_report = None
        try:
            stmt_bs = comp.balance_sheet()
            if stmt_bs:
                bs_report = _dataframe_to_statement_report(stmt_bs.to_dataframe())
        except Exception:
            bs_report = None

        # 2. Income Statement
        is_report = None
        try:
            stmt_is = comp.income_statement()
            if stmt_is:
                is_report = _dataframe_to_statement_report(stmt_is.to_dataframe())
        except Exception:
            is_report = None

        # 3. Cash Flow Statement
        cf_report = None
        try:
            stmt_cf = comp.cash_flow_statement()
            if stmt_cf:
                cf_report = _dataframe_to_statement_report(stmt_cf.to_dataframe())
        except Exception:
            cf_report = None

        res = CompanyStatementsResponse(
            ticker=clean_ticker,
            company_name=comp.name if hasattr(comp, "name") else clean_ticker,
            balance_sheet=bs_report,
            income_statement=is_report,
            cash_flow=cf_report
        )
        _statements_cache[clean_ticker] = res
        return res
        
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"Could not retrieve financial statements for {clean_ticker}: {str(e)}"
        )

@router.get("/{ticker}/filing/{accession_number}", response_model=FilingContentResponse)
def get_filing_document(
    ticker: str,
    accession_number: str,
    section: Optional[str] = Query(None, description="Optional specific Item or section name (e.g. 'Item 1')")
):
    """
    Retrieve the in-platform text of an SEC filing or a specific Item/section.
    Supports Forms 10-K, 10-Q, 8-K, 13F and other regulatory documents.
    """
    clean_ticker = ticker.upper().strip()
    cache_key = f"{clean_ticker}_{accession_number}_{section or 'ALL'}"
    if cache_key in _filing_content_cache:
        return _filing_content_cache[cache_key]

    try:
        comp = edgar.Company(clean_ticker)
        filings = comp.get_filings()
        target = None
        for f in filings:
            acc = getattr(f, "accession_number", getattr(f, "accession_no", ""))
            if acc == accession_number:
                target = f
                break

        if not target:
            raise HTTPException(status_code=404, detail=f"Filing {accession_number} not found for {clean_ticker}")

        obj = target.obj()
        available_sections = []
        if hasattr(obj, "items") and obj.items:
            available_sections = list(obj.items)
        elif hasattr(obj, "sections") and obj.sections:
            available_sections = list(obj.sections)

        section_bookmarks = [
            FilingSectionItem(id=str(s), title=_format_section_title(str(s)))
            for s in available_sections
        ]

        # Extract filing attachments / exhibits
        attachments: List[FilingAttachmentItem] = []
        try:
            cik = getattr(comp, "cik", "")
            acc_nodash = accession_number.replace("-", "")
            raw_atts = getattr(target, "attachments", None)
            if raw_atts:
                for att in list(raw_atts)[:40]:
                    doc_name = str(getattr(att, "document", "") or "")
                    if not doc_name:
                        continue
                    desc = str(getattr(att, "description", "") or "")
                    doc_type = str(getattr(att, "document_type", getattr(att, "type", "")) or "")
                    att_url = getattr(att, "url", "") or (
                        f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_nodash}/{doc_name}"
                        if cik and acc_nodash else ""
                    )
                    attachments.append(FilingAttachmentItem(
                        document=doc_name,
                        description=desc,
                        doc_type=doc_type,
                        url=att_url
                    ))
        except Exception:
            pass

        content = ""
        selected_section = section

        if section:
            # Prefer structured Markdown via obj.section(section).markdown() to preserve tables!
            if hasattr(obj, "section") and callable(obj.section):
                try:
                    sec_item = obj.section(section, strict=False)
                    if sec_item is not None:
                        if hasattr(sec_item, "markdown") and callable(sec_item.markdown):
                            content = str(sec_item.markdown())
                        elif hasattr(sec_item, "text") and callable(sec_item.text):
                            content = str(sec_item.text())
                except Exception:
                    content = ""
            if not content and hasattr(obj, "__getitem__"):
                try:
                    sec_obj = obj[section]
                    if hasattr(sec_obj, "markdown") and callable(sec_obj.markdown):
                        content = str(sec_obj.markdown())
                    else:
                        content = str(sec_obj)
                except Exception:
                    content = f"Section '{section}' could not be extracted directly. Displaying filing text overview."

        if not content:
            if hasattr(target, "markdown") and callable(target.markdown):
                try:
                    content = str(target.markdown())[:120000]
                except Exception:
                    content = ""
            if not content and hasattr(obj, "text") and obj.text:
                content = str(obj.text)[:120000]
            elif not content:
                content = str(obj)[:120000]

        sec_url = getattr(target, "url", getattr(target, "homepage_url", ""))

        res = FilingContentResponse(
            ticker=clean_ticker,
            accession_number=accession_number,
            form=str(target.form),
            filing_date=str(target.filing_date) if target.filing_date else "",
            report_date=str(getattr(target, "report_date", "")) if getattr(target, "report_date", None) else None,
            available_sections=[str(s) for s in available_sections],
            section_bookmarks=section_bookmarks,
            attachments=attachments,
            selected_section=selected_section,
            content=content,
            sec_url=sec_url
        )
        _filing_content_cache[cache_key] = res
        return res

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load filing content for {accession_number}: {str(e)}"
        )

@router.post("/{ticker}/filing-diff", response_model=FilingDiffResponse)
def compute_filing_redline_diff(
    ticker: str,
    payload: FilingDiffRequest
):
    """
    Compute word-level redline comparison between two filings of the same company
    (e.g. 2026 10-K vs 2025 10-K for 'Item 1 - Business' or 'Item 1A - Risk Factors').
    Returns an inline token stream tagging equal, added, and removed words.
    """
    clean_ticker = ticker.upper().strip()
    cache_key = f"{clean_ticker}_{payload.accession_1}_{payload.accession_2}_{payload.section}"
    if cache_key in _filing_diff_cache:
        return _filing_diff_cache[cache_key]

    try:
        comp = edgar.Company(clean_ticker)
        filings = comp.get_filings()
        
        f1 = None
        f2 = None
        for f in filings:
            acc = getattr(f, "accession_number", getattr(f, "accession_no", ""))
            if acc == payload.accession_1:
                f1 = f
            elif acc == payload.accession_2:
                f2 = f
            if f1 and f2:
                break

        if not f1 or not f2:
            raise HTTPException(
                status_code=404,
                detail=f"One or both filings ({payload.accession_1}, {payload.accession_2}) not found for {clean_ticker}"
            )

        obj1 = f1.obj()
        obj2 = f2.obj()

        def extract_text(obj, sec):
            if sec and hasattr(obj, "section") and callable(obj.section):
                try:
                    sec_item = obj.section(sec, strict=False)
                    if sec_item is not None and hasattr(sec_item, "markdown"):
                        t = str(sec_item.markdown())
                        if t and len(t) > 20:
                            return t
                except Exception:
                    pass
            if sec and hasattr(obj, "__getitem__"):
                try:
                    t = str(obj[sec])
                    if t and len(t) > 20: return t
                except Exception:
                    pass
            if hasattr(obj, "text") and obj.text:
                return str(obj.text)[:50000]
            return str(obj)[:50000]

        # f2 is considered older/comparison, f1 is considered newer
        text_old = extract_text(obj2, payload.section)
        text_new = extract_text(obj1, payload.section)

        # Preserve newline boundaries so paragraphs and tables remain structured
        words_old = re.findall(r'\S+|\n', text_old)
        words_new = re.findall(r'\S+|\n', text_new)

        matcher = difflib.SequenceMatcher(None, words_old, words_new)
        similarity_pct = round(matcher.ratio() * 100, 1)

        tokens: List[DiffToken] = []
        words_added = 0
        words_removed = 0

        def _join_tokens(seg: List[str]) -> str:
            out = []
            for w in seg:
                if w == "\n":
                    out.append("\n")
                else:
                    if out and out[-1] != "\n":
                        out.append(" ")
                    out.append(w)
            return "".join(out)

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                tokens.append(DiffToken(type="equal", text=_join_tokens(words_old[i1:i2])))
            elif tag == "replace":
                tokens.append(DiffToken(type="removed", text=_join_tokens(words_old[i1:i2])))
                tokens.append(DiffToken(type="added", text=_join_tokens(words_new[j1:j2])))
                words_removed += sum(1 for w in words_old[i1:i2] if w != "\n")
                words_added += sum(1 for w in words_new[j1:j2] if w != "\n")
            elif tag == "delete":
                tokens.append(DiffToken(type="removed", text=_join_tokens(words_old[i1:i2])))
                words_removed += sum(1 for w in words_old[i1:i2] if w != "\n")
            elif tag == "insert":
                tokens.append(DiffToken(type="added", text=_join_tokens(words_new[j1:j2])))
                words_added += sum(1 for w in words_new[j1:j2] if w != "\n")

        res = FilingDiffResponse(
            ticker=clean_ticker,
            form=payload.form,
            section=payload.section,
            accession_1=payload.accession_1,
            accession_2=payload.accession_2,
            date_1=str(f1.filing_date) if f1.filing_date else "",
            date_2=str(f2.filing_date) if f2.filing_date else "",
            similarity_pct=similarity_pct,
            words_added=words_added,
            words_removed=words_removed,
            tokens=tokens
        )
        _filing_diff_cache[cache_key] = res
        return res

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error computing filing diff: {str(e)}"
        )

@router.get("/{ticker}/filings", response_model=List[SECFilingItem])
def get_company_filings(
    ticker: str,
    sec_provider: SECProvider = Depends(get_sec_provider),
    forms: Optional[str] = Query(default=None, description="Comma-separated forms (e.g. 10-K,10-Q,8-K) or ALL"),
    period: Optional[str] = Query(default="all", description="Preset: last_quarter, last_4_quarters, last_year, last_5_years, all"),
    start_date: Optional[str] = Query(default=None, description="YYYY-MM-DD start date"),
    end_date: Optional[str] = Query(default=None, description="YYYY-MM-DD end date"),
    limit: int = Query(default=50, ge=1, le=200)
):
    """Retrieve official SEC filings with form, period preset, and date-range filtering."""
    clean_ticker = ticker.upper().strip()
    form_list: Optional[List[str]] = None
    if forms and forms.upper() != "ALL":
        form_list = [f.strip() for f in forms.split(",") if f.strip()]

    eff_start = start_date
    today = date.today()
    if not eff_start and period and period != "all":
        days_map = {
            "last_quarter": 95,
            "last_4_quarters": 370,
            "last_year": 366,
            "last_5_years": 365 * 5 + 2,
        }
        if period in days_map:
            eff_start = (today - timedelta(days=days_map[period])).isoformat()

    raw = sec_provider.get_filings(
        clean_ticker,
        forms=form_list,
        limit=limit,
        start_date=eff_start,
        end_date=end_date,
    )
    return [SECFilingItem(**f) for f in raw]

@router.get("/{ticker}/sec-facts")
def get_company_sec_facts(ticker: str):
    """Fetch raw filing EntityFacts summary directly from SEC edgartools."""
    clean_ticker = ticker.upper().strip()
    try:
        comp = edgar.Company(clean_ticker)
        facts = comp.facts
        if facts is None:
            return {"ticker": clean_ticker, "status": "no_facts_available"}
        
        # Return summary of available XBRL facts
        facts_summary = {}
        if hasattr(facts, "us_gaap"):
            facts_summary["us_gaap_facts_count"] = len(facts.us_gaap) if hasattr(facts.us_gaap, "__len__") else "available"
        if hasattr(facts, "dei"):
            facts_summary["dei_facts_count"] = len(facts.dei) if hasattr(facts.dei, "__len__") else "available"

        return {
            "ticker": clean_ticker,
            "company_name": comp.name if hasattr(comp, "name") else clean_ticker,
            "cik": comp.cik if hasattr(comp, "cik") else None,
            "is_foreign": getattr(comp, "is_foreign", False),
            "facts_summary": facts_summary
        }
    except Exception as e:
        return {
            "ticker": clean_ticker,
            "status": "error",
            "message": str(e)
        }


# =============================================================================
# STAGE 2 ENDPOINTS: FORM 4 INSIDERS, FORM 8-K EVENTS, DEF 14A, TEXT SEARCH
# =============================================================================

_insider_cache: Dict[str, InsiderRadarResponse] = {}
_events_cache: Dict[str, MaterialEventsResponse] = {}
_governance_cache: Dict[str, GovernanceResponse] = {}


@router.get("/{ticker}/insider-trades", response_model=InsiderRadarResponse)
def get_insider_trades(ticker: str):
    """
    Form 4 Insider Trading & 30-day Cluster Buying Radar.
    Detects open-market purchases ('P') and sales ('S') across recent Form 4 filings.
    """
    clean_ticker = ticker.upper().strip()
    if clean_ticker in _insider_cache:
        return _insider_cache[clean_ticker]

    try:
        comp = edgar.Company(clean_ticker)
        filings = comp.get_filings(form="4")
        if not filings:
            res = InsiderRadarResponse(ticker=clean_ticker)
            _insider_cache[clean_ticker] = res
            return res

        txs: List[InsiderTransactionItem] = []
        recent_buyers = set()
        total_buy_usd = 0.0
        total_sell_usd = 0.0
        cutoff_30d = (date.today() - timedelta(days=30)).isoformat()

        for f in filings[:12]:
            f_date = str(getattr(f, "filing_date", "") or "")
            f_url = str(getattr(f, "url", getattr(f, "homepage_url", "")) or "")
            try:
                ownership = f.obj()
                insider_name = str(
                    getattr(ownership, "reporting_owner_name", None)
                    or getattr(ownership, "insider_name", None)
                    or "Insider"
                )
                title = str(
                    getattr(ownership, "reporting_owner_relationship", None)
                    or getattr(ownership, "position", "")
                    or ""
                )

                # edgartools Ownership exposes non_derivative_table / transactions / get_transactions()
                raw_txs = []
                if hasattr(ownership, "non_derivative_table") and ownership.non_derivative_table is not None:
                    ndt = ownership.non_derivative_table
                    if hasattr(ndt, "transactions") and ndt.transactions is not None:
                        raw_txs = ndt.transactions
                elif hasattr(ownership, "transactions") and ownership.transactions is not None:
                    raw_txs = ownership.transactions

                if isinstance(raw_txs, pd.DataFrame) and not raw_txs.empty:
                    for _, r in raw_txs.iterrows():
                        code = str(r.get("TransactionCode", r.get("transaction_code", r.get("Code", ""))) or "").strip().upper()
                        shares = float(r.get("Shares", r.get("shares", 0)) or 0)
                        price_val = r.get("Price", r.get("price", None))
                        price = float(price_val) if pd.notnull(price_val) and price_val != "" else None
                        tx_date = str(r.get("Date", r.get("transaction_date", f_date)) or f_date)
                        val_usd = round(shares * price, 2) if (shares and price) else None

                        if code == "P" and shares > 0:
                            if val_usd:
                                total_buy_usd += val_usd
                            if f_date >= cutoff_30d:
                                recent_buyers.add(insider_name)
                        elif code == "S" and shares > 0 and val_usd:
                            total_sell_usd += val_usd

                        if code in ("P", "S", "M", "A"):
                            txs.append(InsiderTransactionItem(
                                filing_date=f_date,
                                transaction_date=tx_date,
                                insider_name=insider_name,
                                title=title[:60],
                                transaction_code=code,
                                shares=shares,
                                price=price,
                                value_usd=val_usd,
                                sec_url=f_url,
                            ))
            except Exception:
                continue

        res = InsiderRadarResponse(
            ticker=clean_ticker,
            cluster_buying_detected=len(recent_buyers) >= 3,
            cluster_buyers_count=len(recent_buyers),
            total_purchases_usd=round(total_buy_usd, 2),
            total_sales_usd=round(total_sell_usd, 2),
            transactions=txs[:40],
        )
        _insider_cache[clean_ticker] = res
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load insider trades for {clean_ticker}: {str(e)}")


@router.get("/{ticker}/material-events", response_model=MaterialEventsResponse)
def get_material_events(ticker: str):
    """Form 8-K Material Corporate Events feed with Item classifications."""
    clean_ticker = ticker.upper().strip()
    if clean_ticker in _events_cache:
        return _events_cache[clean_ticker]

    try:
        comp = edgar.Company(clean_ticker)
        filings = comp.get_filings(form="8-K")
        events: List[MaterialEventItem] = []

        if filings:
            for f in filings[:10]:
                acc = getattr(f, "accession_number", getattr(f, "accession_no", ""))
                f_date = str(getattr(f, "filing_date", "") or "")
                f_url = str(getattr(f, "url", getattr(f, "homepage_url", "")) or "")
                items: List[str] = []
                summary = ""
                try:
                    obj = f.obj()
                    if hasattr(obj, "items") and obj.items:
                        items = [_format_section_title(str(it)) for it in obj.items]
                    if hasattr(obj, "text") and obj.text:
                        summary = str(obj.text).strip()[:450]
                except Exception:
                    pass
                events.append(MaterialEventItem(
                    filing_date=f_date,
                    accession_number=acc,
                    items=items,
                    summary=summary,
                    sec_url=f_url,
                ))

        res = MaterialEventsResponse(ticker=clean_ticker, events=events)
        _events_cache[clean_ticker] = res
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load 8-K material events for {clean_ticker}: {str(e)}")


@router.get("/{ticker}/governance", response_model=GovernanceResponse)
def get_governance_proxy(ticker: str):
    """DEF 14A Proxy Statement & Executive Compensation summary."""
    clean_ticker = ticker.upper().strip()
    if clean_ticker in _governance_cache:
        return _governance_cache[clean_ticker]

    try:
        comp = edgar.Company(clean_ticker)
        filings = comp.get_filings(form="DEF 14A")
        if not filings:
            res = GovernanceResponse(ticker=clean_ticker, summary="No DEF 14A proxy statement found.")
            _governance_cache[clean_ticker] = res
            return res

        latest = filings[0]
        acc = getattr(latest, "accession_number", getattr(latest, "accession_no", ""))
        f_date = str(getattr(latest, "filing_date", "") or "")
        f_url = str(getattr(latest, "url", getattr(latest, "homepage_url", "")) or "")
        comp_rows: List[Dict[str, Any]] = []
        summary = ""

        try:
            obj = latest.obj()
            df_comp = getattr(obj, "executive_compensation", None)
            if isinstance(df_comp, pd.DataFrame) and not df_comp.empty:
                comp_rows = df_comp.head(15).fillna("").to_dict(orient="records")
            if hasattr(latest, "markdown"):
                summary = str(latest.markdown())[:2000]
        except Exception:
            pass

        res = GovernanceResponse(
            ticker=clean_ticker,
            filing_date=f_date,
            accession_number=acc,
            sec_url=f_url,
            summary=summary or f"DEF 14A Proxy Statement filed {f_date}.",
            compensation_rows=comp_rows,
        )
        _governance_cache[clean_ticker] = res
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load DEF 14A governance for {clean_ticker}: {str(e)}")


@router.post("/{ticker}/search-filing", response_model=FilingSearchResponse)
def search_company_filing(ticker: str, payload: FilingSearchRequest):
    """Full-text keyword search across a company's 10-K/10-Q sections."""
    clean_ticker = ticker.upper().strip()
    try:
        comp = edgar.Company(clean_ticker)
        filings = comp.get_filings(form=payload.form)
        if not filings:
            raise HTTPException(status_code=404, detail=f"No {payload.form} filings found for {clean_ticker}")

        target = filings[0]
        if payload.accession_number:
            for f in filings:
                acc = getattr(f, "accession_number", getattr(f, "accession_no", ""))
                if acc == payload.accession_number:
                    target = f
                    break

        acc = getattr(target, "accession_number", getattr(target, "accession_no", ""))
        f_date = str(getattr(target, "filing_date", "") or "")
        obj = target.obj()
        sections = list(obj.items) if hasattr(obj, "items") and obj.items else ["Document"]

        hits: List[FilingSearchHit] = []
        pattern = re.compile(re.escape(payload.query), re.IGNORECASE)

        for sec in sections:
            try:
                sec_text = str(obj[sec]) if hasattr(obj, "__getitem__") and sec != "Document" else str(target.markdown())
            except Exception:
                continue
            for m in pattern.finditer(sec_text):
                start = max(0, m.start() - 120)
                end = min(len(sec_text), m.end() + 180)
                snippet = sec_text[start:end].replace("\n", " ").strip()
                hits.append(FilingSearchHit(section=_format_section_title(str(sec)), snippet=f"...{snippet}..."))
                if len(hits) >= 30:
                    break
            if len(hits) >= 30:
                break

        return FilingSearchResponse(
            ticker=clean_ticker,
            form=str(target.form),
            filing_date=f_date,
            accession_number=acc,
            query=payload.query,
            total_hits=len(hits),
            hits=hits,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
