import pandas as pd
import numpy as np
from typing import Dict, Any, List
from ..data.schemas import FinancialStatement, MarketData

class SafetyModel:
    """Calculates safety signals and statistical outliers for companies."""

    def calculate_traffic_light(self, fs: FinancialStatement, md: MarketData) -> str:
        """
        Calculates a 'Traffic Light' (Output) signal based on liquidity and leverage.
        
        Criteria:
        - GREEN: Quick Ratio >= 2 & D/E <= 0.33 & Debt/Assets <= 0.2
        - YELLOW: Quick Ratio >= 1 & D/E <= 1 & Debt/Assets <= 0.35
        - RED: Otherwise
        """
        # Calculate Ratios
        total_debt = (fs.short_term_debt or 0) + (fs.long_term_debt or 0)
        
        # Quick Ratio = (Current Assets - Inventory) / Current Liabilities
        # Fallback to current ratio if liabilities are 0
        quick_ratio = 0.0
        if fs.current_liabilities > 0:
            quick_ratio = ((fs.current_assets or 0) - (fs.inventory or 0)) / fs.current_liabilities
        
        # Debt to Equity
        debt_to_equity = 0.0
        if fs.shareholders_equity and fs.shareholders_equity > 0:
            debt_to_equity = total_debt / fs.shareholders_equity
        else:
            debt_to_equity = 999.0 # High penalty for no equity
            
        # Debt to Assets
        debt_to_assets = 0.0
        if fs.total_assets and fs.total_assets > 0:
            debt_to_assets = total_debt / fs.total_assets

        # Traffic Light Logic
        if quick_ratio >= 2.0 and debt_to_equity <= 0.33 and debt_to_assets <= 0.2:
            return "GREEN"
        
        if quick_ratio >= 1.0 and debt_to_equity <= 1.0 and debt_to_assets <= 0.35:
            return "YELLOW"
            
        return "RED"

    def calculate_revenue_zscore_label(self, revenue_history: Dict[str, float]) -> str:
        """
        Calculates if the most recent revenue is an outlier based on Z-Score.
        Returns 'High', 'Normal', 'Low', or 'N/A'.
        
        Criteria: Outlier if most recent is > 2 Std Dev from the mean of last 8 periods.
        """
        if not revenue_history or len(revenue_history) < 2:
            return "N/A"
            
        # Sort history by date descending and get values
        dates = sorted(revenue_history.keys(), reverse=True)
        values = [revenue_history[d] for d in dates if revenue_history[d] > 0]
        
        if len(values) < 2:
            return "N/A"
            
        most_recent = values[0]
        mean = np.mean(values)
        std = np.std(values)
        
        if std == 0:
            return "Normal"
            
        z_score = (most_recent - mean) / std
        
        if z_score > 2:
            return "High"
        elif z_score < -2:
            return "Low"
        else:
            return "Normal"

    def calculate_working_capital_anomaly(
        self,
        current_rev: float,
        prev_rev: float,
        current_ar: float,
        prev_ar: float,
        current_inv: float = 0.0,
        prev_inv: float = 0.0
    ) -> Dict[str, Any]:
        """
        Detects anomalies in working capital growth vs top-line revenue growth.
        Criteria:
        - WARNING: Div_AR > 15% (with positive AR growth) or Div_Inv > 15% (with positive Inv growth)
        - ELEVATED: Div_AR > 10% (with positive AR growth) or Div_Inv > 10% (with positive Inv growth)
        - NORMAL: Growth aligns within expected operational variance (+/- 10%)
        - N/A: Insufficient or non-positive baseline comparative data
        """
        if prev_rev is None or prev_rev <= 0 or prev_ar is None or prev_ar <= 0:
            return {
                "wc_anomaly_signal": "N/A",
                "ar_growth": 0.0,
                "rev_growth": 0.0,
                "inv_growth": 0.0,
                "ar_divergence": 0.0,
                "inv_divergence": 0.0
            }

        rev_growth = (current_rev - prev_rev) / prev_rev
        ar_growth = (current_ar - prev_ar) / prev_ar
        ar_divergence = ar_growth - rev_growth

        has_inv = (prev_inv is not None and prev_inv > 0 and current_inv is not None and current_inv > 0)
        if has_inv:
            inv_growth = (current_inv - prev_inv) / prev_inv
            inv_divergence = inv_growth - rev_growth
        else:
            inv_growth = 0.0
            inv_divergence = 0.0

        # Divergence flags
        is_warning = (ar_divergence > 0.15 and ar_growth > 0) or (has_inv and inv_divergence > 0.15 and inv_growth > 0)
        is_elevated = (ar_divergence > 0.10 and ar_growth > 0) or (has_inv and inv_divergence > 0.10 and inv_growth > 0)

        if is_warning:
            signal = "WARNING"
        elif is_elevated:
            signal = "ELEVATED"
        else:
            signal = "NORMAL"

        return {
            "wc_anomaly_signal": signal,
            "ar_growth": round(ar_growth * 100, 2),
            "rev_growth": round(rev_growth * 100, 2),
            "inv_growth": round(inv_growth * 100, 2) if has_inv else 0.0,
            "ar_divergence": round(ar_divergence * 100, 2),
            "inv_divergence": round(inv_divergence * 100, 2) if has_inv else 0.0
        }

