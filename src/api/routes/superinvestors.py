from fastapi import APIRouter, HTTPException
from typing import Dict, List
import pandas as pd
import edgar

from src.api.schemas.superinvestors import (
    SuperinvestorProfile,
    SuperinvestorHolding,
    SuperinvestorPortfolioResponse,
)

router = APIRouter(prefix="/api/superinvestors", tags=["Superinvestors (13F)"])

_superinvestor_cache: Dict[str, SuperinvestorPortfolioResponse] = {}

SUPERINVESTORS: List[SuperinvestorProfile] = [
    SuperinvestorProfile(
        cik="0001067983",
        manager="Warren Buffett",
        fund_name="Berkshire Hathaway Inc.",
        style="Quality Compounders & Intrinsic Value",
        note="US 13F holdings only; non-US stakes (e.g. Japanese trading houses) are reported outside 13F."
    ),
    SuperinvestorProfile(
        cik="0001061768",
        manager="Seth Klarman",
        fund_name="The Baupost Group, L.L.C.",
        style="Deep Value & Special Situations",
    ),
    SuperinvestorProfile(
        cik="0001709323",
        manager="Li Lu",
        fund_name="Himalaya Capital Management LLC",
        style="Concentrated Long-Term Value",
        note="13F reflects US-listed equities; Asian holdings are tracked separately."
    ),
    SuperinvestorProfile(
        cik="0001549575",
        manager="Mohnish Pabrai",
        fund_name="Dalal Street, LLC",
        style="Dhandho (Low-Risk, High-Uncertainty Value)",
    ),
    SuperinvestorProfile(
        cik="0000949509",
        manager="Howard Marks",
        fund_name="Oaktree Capital Management, L.P.",
        style="Distressed Debt & Contrarian Value",
    ),
    SuperinvestorProfile(
        cik="0001336528",
        manager="Bill Ackman",
        fund_name="Pershing Square Capital Management, L.P.",
        style="Concentrated Activist Quality Value",
    ),
    SuperinvestorProfile(
        cik="0001079114",
        manager="David Einhorn",
        fund_name="Greenlight Capital, Inc.",
        style="Value & Catalyst-Driven Equities",
    ),
    SuperinvestorProfile(
        cik="0001510387",
        manager="Joel Greenblatt",
        fund_name="Gotham Asset Management, LLC",
        style="Magic Formula Quantitative Value",
    ),
    SuperinvestorProfile(
        cik="0000915191",
        manager="Prem Watsa",
        fund_name="Fairfax Financial Holdings Ltd.",
        style="Insurance Float & Deep Value",
    ),
    SuperinvestorProfile(
        cik="0001112520",
        manager="Chuck Akre",
        fund_name="Akre Capital Management, LLC",
        style="Three-Legged Stool Compounders",
    ),
    SuperinvestorProfile(
        cik="0001096343",
        manager="Tom Gayner",
        fund_name="Markel Group Inc.",
        style="Quality Value Compounders",
    ),
    SuperinvestorProfile(
        cik="0000732905",
        manager="Tweedy, Browne",
        fund_name="Tweedy, Browne Company LLC",
        style="Graham-and-Dodd Deep Value",
    ),
]


def _extract_13f_df(filing) -> pd.DataFrame:
    """Safely extract holdings DataFrame from an edgartools 13F-HR filing."""
    obj = filing.obj() if hasattr(filing, "obj") else None
    if obj is None and hasattr(filing, "thirteenf"):
        obj = filing.thirteenf()
    if obj is None:
        return pd.DataFrame()
    for attr in ("holdings", "infotable", "holdings_data"):
        df = getattr(obj, attr, None)
        if isinstance(df, pd.DataFrame) and not df.empty:
            return df.copy()
    return pd.DataFrame()


@router.get("/list", response_model=List[SuperinvestorProfile])
def list_superinvestors():
    """Return curated roster of renowned Value Investing Superinvestors."""
    return SUPERINVESTORS


@router.get("/{cik}", response_model=SuperinvestorPortfolioResponse)
def get_superinvestor_portfolio(cik: str):
    """
    Retrieve the latest SEC Form 13F-HR holdings for a superinvestor by CIK,
    computing portfolio weights and quarter-over-quarter share changes.
    Results are cached in memory.
    """
    clean_cik = cik.strip().zfill(10)
    if clean_cik in _superinvestor_cache:
        return _superinvestor_cache[clean_cik]

    profile = next((s for s in SUPERINVESTORS if s.cik == clean_cik), None)
    if not profile:
        profile = SuperinvestorProfile(
            cik=clean_cik,
            manager=f"Manager {clean_cik}",
            fund_name=f"Institutional Manager ({clean_cik})",
            style="13F Institutional Filer",
        )

    try:
        comp = edgar.Company(clean_cik)
        filings = comp.get_filings(form="13F-HR")
        if not filings or len(filings) == 0:
            raise HTTPException(status_code=404, detail=f"No 13F-HR filings found for CIK {clean_cik}")

        latest = filings[0]
        df_curr = _extract_13f_df(latest)
        if df_curr.empty:
            raise HTTPException(status_code=404, detail=f"13F-HR holdings table empty for CIK {clean_cik}")

        # Previous quarter for QoQ diff
        prev_map: Dict[str, float] = {}
        prev_period = None
        if len(filings) > 1:
            try:
                prev = filings[1]
                prev_period = str(getattr(prev, "report_date", "") or getattr(prev, "filing_date", ""))
                df_prev = _extract_13f_df(prev)
                if not df_prev.empty:
                    cusip_col_p = next((c for c in df_prev.columns if c.lower() == "cusip"), None)
                    shares_col_p = next((c for c in df_prev.columns if "share" in c.lower() or c.lower() == "sshprnamt"), None)
                    if cusip_col_p and shares_col_p:
                        grouped = df_prev.groupby(cusip_col_p)[shares_col_p].sum()
                        prev_map = {str(k).strip(): float(v) for k, v in grouped.items() if pd.notnull(v)}
            except Exception:
                pass

        # Identify columns flexibly across edgartools versions
        cusip_col = next((c for c in df_curr.columns if c.lower() == "cusip"), None)
        ticker_col = next((c for c in df_curr.columns if c.lower() == "ticker"), None)
        issuer_col = next((c for c in df_curr.columns if c.lower() in ("issuer", "name of issuer", "nameofissuer", "company")), None)
        shares_col = next((c for c in df_curr.columns if "share" in c.lower() or c.lower() == "sshprnamt"), None)
        val_col = next((c for c in df_curr.columns if c.lower() in ("value", "val", "market_value")), None)

        if not issuer_col or not val_col:
            raise HTTPException(status_code=500, detail=f"Unexpected 13F column schema: {list(df_curr.columns)}")

        # Aggregate by CUSIP or Issuer (13F filings often split by manager sub-accounts)
        group_key = cusip_col if cusip_col else issuer_col
        agg_dict = {val_col: "sum", issuer_col: "first"}
        if shares_col:
            agg_dict[shares_col] = "sum"
        if ticker_col:
            agg_dict[ticker_col] = "first"

        df_agg = df_curr.groupby(group_key, as_index=False).agg(agg_dict)
        df_agg = df_agg.sort_values(by=val_col, ascending=False)

        # edgartools normalizes 13F value to USD or thousands depending on version; detect cleanly
        raw_total = float(df_agg[val_col].sum())
        # SEC 13F XML switched from $1000s to $1s in 2023; edgartools Value is usually in USD (or $1000s if < 1e8 for Berkshire)
        multiplier = 1.0
        if raw_total > 0 and raw_total < 500_000_000 and clean_cik == "0001067983":
            multiplier = 1000.0
        total_val = raw_total * multiplier

        holdings: List[SuperinvestorHolding] = []
        for _, row in df_agg.head(100).iterrows():
            val_usd = float(row[val_col] or 0.0) * multiplier
            shares = float(row[shares_col] or 0.0) if shares_col else 0.0
            cusip = str(row[cusip_col]).strip() if cusip_col and pd.notnull(row[cusip_col]) else ""
            ticker_val = str(row[ticker_col]).strip() if ticker_col and pd.notnull(row[ticker_col]) else None
            if ticker_val in ("", "None", "nan", "N/A"):
                ticker_val = None
            issuer = str(row[issuer_col] or "Unknown").strip()
            weight = round((val_usd / total_val) * 100, 2) if total_val > 0 else 0.0

            activity = "HELD"
            change_pct = None
            if prev_map and cusip:
                prev_sh = prev_map.get(cusip, 0.0)
                if prev_sh == 0 and shares > 0:
                    activity = "NEW"
                    change_pct = 100.0
                elif prev_sh > 0:
                    pct = ((shares - prev_sh) / prev_sh) * 100
                    change_pct = round(pct, 1)
                    if pct > 1.0:
                        activity = "ADDED"
                    elif pct < -1.0:
                        activity = "REDUCED"
                    else:
                        activity = "UNCHANGED"

            holdings.append(SuperinvestorHolding(
                cusip=cusip,
                ticker=ticker_val,
                issuer=issuer,
                shares=shares,
                value_usd=val_usd,
                weight_pct=weight,
                activity=activity,
                share_change_pct=change_pct,
            ))

        res = SuperinvestorPortfolioResponse(
            cik=clean_cik,
            manager=profile.manager,
            fund_name=getattr(comp, "name", None) or profile.fund_name,
            style=profile.style,
            filing_date=str(getattr(latest, "filing_date", "") or ""),
            report_period=str(getattr(latest, "report_date", "") or ""),
            previous_report_period=prev_period,
            total_value_usd=total_val,
            holdings_count=len(df_agg),
            sec_url=str(getattr(latest, "url", getattr(latest, "homepage_url", "")) or ""),
            holdings=holdings,
        )
        _superinvestor_cache[clean_cik] = res
        return res

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch 13F portfolio for {clean_cik}: {str(e)}")
