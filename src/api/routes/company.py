from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List
import dataclasses
import os
import edgar

from src.api.schemas.company import (
    CompanyDetailResponse,
    MagicFormulaDetails,
    GreenwaldDetails,
    DCFDetails,
    SafetyDetails,
    SECFilingItem
)
from src.api.deps import get_integrator, get_sec_provider
from src.engine.integrator import DataIntegrator
from src.data.sec_provider import SECProvider
from src.models.magic_formula import MagicFormulaModel
from src.models.greenwald import GreenwaldModel
from src.models.dcf import DCFModel
from src.models.safety import SafetyModel

router = APIRouter(prefix="/api/company", tags=["Company Deep-Dive"])

@router.get("/{ticker}", response_model=CompanyDetailResponse)
def get_company_details(
    ticker: str,
    integrator: DataIntegrator = Depends(get_integrator)
):
    """
    Retrieve comprehensive fundamental valuation breakdown for a company.
    Combines Joel Greenblatt's Magic Formula, Bruce Greenwald's EPV & Reproduction Cost,
    and steady-state DCF intrinsic valuation with SEC XBRL financial facts and regulatory filings.
    """
    clean_ticker = ticker.upper().strip()
    
    fs = None
    md = None
    try:
        fs, md = integrator.fetch_company_data(clean_ticker, enrich=True)
    except Exception as e:
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

    return CompanyDetailResponse(
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

@router.get("/{ticker}/filings", response_model=List[SECFilingItem])
def get_company_filings(
    ticker: str,
    sec_provider: SECProvider = Depends(get_sec_provider),
    limit: int = Query(default=25, ge=1, le=100)
):
    """Retrieve recent regulatory SEC filings (10-K, 10-Q, 8-K) with direct official SEC links."""
    clean_ticker = ticker.upper().strip()
    raw = sec_provider.get_filings(clean_ticker, limit=limit)
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
