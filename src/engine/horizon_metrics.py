"""
Multi-horizon valuation & performance analytics (TTM, 3Y, 5Y, 10Y):
- Total Return to Shareholders (TRS = Price Appreciation % + Cumulative Dividend Yield %)
- ROIC = EBIT * (1 - Effective Tax Rate) / (Inventory + Receivables - Payables + Net Fixed Assets)
- Revenue Growth CAGR (%)
- FCFF TTM & 5-Year Average FCFF Payback
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import yfinance as yf
import edgar


def _safe_num(val: Any) -> float:
    try:
        if val is None or pd.isna(val):
            return 0.0
        return float(val)
    except Exception:
        return 0.0


def _compute_trs_from_yfinance(ticker: str) -> Dict[str, Tuple[Optional[float], Optional[float], Optional[float]]]:
    """
    Return {horizon: (price_return_pct, dividend_yield_pct, total_return_pct)}
    for horizons TTM (1Y), 3Y, 5Y, 10Y.
    """
    out: Dict[str, Tuple[Optional[float], Optional[float], Optional[float]]] = {
        "TTM": (None, None, None),
        "3Y": (None, None, None),
        "5Y": (None, None, None),
        "10Y": (None, None, None),
    }
    try:
        hist = yf.Ticker(ticker).history(period="10y", actions=True, auto_adjust=False)
        if hist is None or hist.empty or "Close" not in hist.columns:
            return out

        hist = hist.dropna(subset=["Close"])
        if hist.empty:
            return out

        p_end = float(hist["Close"].iloc[-1])
        end_dt = hist.index[-1]
        has_div = "Dividends" in hist.columns

        for label, years in (("TTM", 1), ("3Y", 3), ("5Y", 5), ("10Y", 10)):
            cutoff = end_dt - pd.Timedelta(days=365 * years)
            sub = hist[hist.index >= cutoff]
            if len(sub) < 5:
                continue
            # Require at least 75% of requested window to avoid mislabeling IPOs as 10Y
            actual_days = (end_dt - sub.index[0]).days
            if years > 1 and actual_days < 365 * years * 0.75:
                continue
            p_start = float(sub["Close"].iloc[0])
            if p_start <= 0:
                continue
            price_ret = ((p_end - p_start) / p_start) * 100.0
            div_sum = float(sub["Dividends"].sum()) if has_div else 0.0
            div_ret = (div_sum / p_start) * 100.0
            out[label] = (round(price_ret, 2), round(div_ret, 2), round(price_ret + div_ret, 2))
    except Exception:
        pass
    return out


def _extract_row_series(df: Optional[pd.DataFrame], period_cols: List[str], keywords: Tuple[str, ...]) -> Dict[str, float]:
    """Extract {period: value} for the first matching US-GAAP concept/label keyword."""
    if df is None or df.empty:
        return {}
    df_c = df.copy()
    if "concept" not in df_c.columns:
        df_c = df_c.reset_index()

    for kw in keywords:
        kw_low = kw.lower()
        mask = df_c["concept"].astype(str).str.lower().str.contains(kw_low, na=False)
        if not mask.any() and "label" in df_c.columns:
            mask = df_c["label"].astype(str).str.lower().str.contains(kw_low, na=False)
        if mask.any():
            row = df_c[mask].iloc[0]
            return {p: _safe_num(row.get(p)) for p in period_cols}
    return {}


def compute_company_horizon_metrics(
    ticker: str,
    fs_dict: Dict[str, Any],
    market_cap: float,
) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float], List[Dict[str, Any]]]:
    """
    Compute (fcff_ttm, mc_to_fcff_ttm, fcff_5y_avg, mc_to_fcff_5y_avg, horizon_metrics_list).
    """
    ebit_ttm = _safe_num(fs_dict.get("ebit"))
    ocf_ttm = _safe_num(fs_dict.get("operating_cash_flow"))
    capex_ttm = abs(_safe_num(fs_dict.get("capex")))
    int_ttm = abs(_safe_num(fs_dict.get("interest_expense_ttm")))
    tax_ttm = _safe_num(fs_dict.get("income_tax_expense_ttm"))
    pretax_ttm = ebit_ttm - int_ttm
    eff_tax_ttm = max(0.0, min(0.35, tax_ttm / pretax_ttm)) if pretax_ttm > 0 and tax_ttm > 0 else 0.25

    raw_fcf_ttm = _safe_num(fs_dict.get("free_cash_flow"))
    if ocf_ttm != 0:
        fcff_ttm = ocf_ttm - (int_ttm * (1.0 - eff_tax_ttm)) - capex_ttm
    elif raw_fcf_ttm != 0:
        fcff_ttm = raw_fcf_ttm - (int_ttm * (1.0 - eff_tax_ttm))
    else:
        fcff_ttm = None

    mc_to_fcff_ttm = round(market_cap / fcff_ttm, 2) if fcff_ttm and fcff_ttm > 0 and market_cap > 0 else None

    # TTM ROIC = EBIT * (1 - tax) / (Inventory + AR - AP + Net Fixed Assets)
    inv_ttm = _safe_num(fs_dict.get("inventory"))
    ar_ttm = _safe_num(fs_dict.get("accounts_receivable"))
    ap_ttm = _safe_num(fs_dict.get("accounts_payable"))
    nfa_ttm = _safe_num(fs_dict.get("net_fixed_assets"))
    ic_ttm = inv_ttm + ar_ttm - ap_ttm + nfa_ttm
    roic_ttm = round((ebit_ttm * (1.0 - eff_tax_ttm) / ic_ttm) * 100.0, 2) if ic_ttm > 0 and ebit_ttm != 0 else None

    # Fetch TRS from yfinance
    trs_map = _compute_trs_from_yfinance(ticker)

    # Fetch up to 10 years of annual statements from edgartools for 3Y/5Y/10Y ROIC, Rev CAGR, FCFF 5Y Avg
    annual_fcff: List[float] = []
    annual_roic: List[float] = []
    annual_rev: List[float] = []
    try:
        comp = edgar.Company(ticker)
        is_stmt = comp.income_statement(periods=10)
        bs_stmt = comp.balance_sheet(periods=10)
        cf_stmt = comp.cash_flow_statement(periods=10)

        meta_cols = {
            "concept", "label", "depth", "is_abstract", "is_total", "section", "confidence",
            "level", "abstract", "dimension", "is_breakdown", "dimension_axis", "dimension_member",
            "dimension_member_label", "dimension_label", "balance", "weight", "preferred_sign",
            "parent_concept", "parent_abstract_concept",
        }

        is_df = is_stmt.to_dataframe() if is_stmt else None
        bs_df = bs_stmt.to_dataframe() if bs_stmt else None
        cf_df = cf_stmt.to_dataframe() if cf_stmt else None

        if is_df is not None and not is_df.empty:
            p_cols = sorted([c for c in is_df.columns if c not in meta_cols], reverse=True)
            revs = _extract_row_series(is_df, p_cols, ("revenues", "revenuefromcontract", "salesrevenue"))
            ebits = _extract_row_series(is_df, p_cols, ("operatingincomeloss",))
            ints = _extract_row_series(is_df, p_cols, ("interestexpense",))
            taxes = _extract_row_series(is_df, p_cols, ("incometaxexpense",))

            ocfs = _extract_row_series(cf_df, p_cols, ("netcashprovidedbyusedinoperatingactivities", "operatingactivities"))
            capexs = _extract_row_series(cf_df, p_cols, ("paymentstoacquirepropertyplantandequipment", "capitalexpenditures"))

            invs = _extract_row_series(bs_df, p_cols, ("inventorynet", "inventories"))
            ars = _extract_row_series(bs_df, p_cols, ("accountsreceivable",))
            aps = _extract_row_series(bs_df, p_cols, ("accountspayable",))
            nfas = _extract_row_series(bs_df, p_cols, ("propertyplantandequipmentnet",))

            for p in p_cols:
                r_val = revs.get(p, 0.0)
                if r_val > 0:
                    annual_rev.append(r_val)
                eb = ebits.get(p, 0.0)
                it = abs(ints.get(p, 0.0))
                tx = taxes.get(p, 0.0)
                pt = eb - it
                tx_rate = max(0.0, min(0.35, tx / pt)) if pt > 0 and tx > 0 else 0.25

                oc = ocfs.get(p, 0.0)
                cx = abs(capexs.get(p, 0.0))
                if oc != 0:
                    annual_fcff.append(oc - it * (1.0 - tx_rate) - cx)

                ic = invs.get(p, 0.0) + ars.get(p, 0.0) - aps.get(p, 0.0) + nfas.get(p, 0.0)
                if ic > 0 and eb != 0:
                    annual_roic.append((eb * (1.0 - tx_rate) / ic) * 100.0)
    except Exception:
        pass

    fcff_5y_avg = round(sum(annual_fcff[:5]) / len(annual_fcff[:5]), 2) if len(annual_fcff) >= 2 else fcff_ttm
    mc_to_fcff_5y_avg = round(market_cap / fcff_5y_avg, 2) if fcff_5y_avg and fcff_5y_avg > 0 and market_cap > 0 else None

    def _rev_cagr(n_years: int) -> Optional[float]:
        if len(annual_rev) >= 2:
            idx = min(n_years, len(annual_rev) - 1)
            if idx >= 1 and annual_rev[idx] > 0 and annual_rev[0] > 0:
                cagr = ((annual_rev[0] / annual_rev[idx]) ** (1.0 / idx) - 1.0) * 100.0
                return round(cagr, 2)
        return None

    def _avg_slice(vals: List[float], n: int) -> Optional[float]:
        s = vals[:n]
        return round(sum(s) / len(s), 2) if s else None

    horizons: List[Dict[str, Any]] = []
    for label, n_yrs in (("TTM", 1), ("3Y", 3), ("5Y", 5), ("10Y", 10)):
        pr, dr, tr = trs_map.get(label, (None, None, None))
        if label == "TTM":
            roic_v = roic_ttm
            fcff_v = round(fcff_ttm, 2) if fcff_ttm is not None else None
            payback_v = mc_to_fcff_ttm
        else:
            roic_v = _avg_slice(annual_roic, n_yrs)
            fcff_v = _avg_slice(annual_fcff, n_yrs)
            payback_v = round(market_cap / fcff_v, 2) if fcff_v and fcff_v > 0 and market_cap > 0 else None

        horizons.append({
            "horizon": label,
            "price_return_pct": pr,
            "dividend_yield_pct": dr,
            "total_return_pct": tr,
            "roic_pct": roic_v,
            "revenue_cagr_pct": _rev_cagr(n_yrs),
            "fcff": fcff_v,
            "mc_to_fcff": payback_v,
        })

    return (
        round(fcff_ttm, 2) if fcff_ttm is not None else None,
        mc_to_fcff_ttm,
        fcff_5y_avg,
        mc_to_fcff_5y_avg,
        horizons,
    )
