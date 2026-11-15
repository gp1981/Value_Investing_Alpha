import pandas as pd
import numpy as np
from typing import Dict, Any

class EquityAnalysisModel:
    """
    Implements equity recalculation and CAGR metrics based on historical data.
    Resolves GitHub Issue #10.
    """
    
    def calculate_metrics(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Calculates Full Equity variants and their CAGRs.
        
        Input df columns expected:
        - date (datetime)
        - equity
        - net_income
        - dividends (usually negative for outflow)
        - repurchases (usually negative for outflow)
        - issuances (positive for inflow)
        - total_debt
        """
        if df.empty or len(df) < 2:
            return {}
            
        # Ensure sorted by date
        df = df.sort_values("date")
        
        # Calculate time elapsed
        first_date = df['date'].iloc[0]
        last_date = df['date'].iloc[-1]
        years_elapsed = (last_date - first_date).days / 365.25
        
        if years_elapsed <= 0:
            return {}

        # 1. Option 1: Full Equity (Standard)
        # Add back dividends and net repurchases
        # Note: In CF, outflows like dividends and repurchases are often reported as negative.
        # We need to treat them as additive to "reconstruct" what equity would have been.
        # So: Reconstructed = Current + Sum(|outflows|) - Sum(inflows)
        
        # We calculate cumulative sums
        # If the input values are already negative, we use their absolute values for "add back"
        # Or more simply, if they are outflows, we subtract them from current equity to see 
        # how much was "lost" from equity.
        
        # Let's align with the R script logic:
        # cum_dividends = cumsum(divs)
        # cum_repurchased = cumsum(repurchases)
        # cum_issued = cumsum(issuances)
        
        # full_equity = current_equity - cum_dividends - cum_issued - cum_repurchased
        # (Assuming divs and repurchases are negative)
        
        # Let's use absolute logic to be safe:
        # We'll treat outflows as positive amounts paid out.
        divs_paid = abs(df['dividends'].sum())
        repurchased_net = abs(df['repurchases'].sum()) - df['issuances'].sum()
        
        initial_equity = df['equity'].iloc[0]
        last_equity = df['equity'].iloc[-1]
        
        # Variant 1: Full Equity (Standard) - Dividends and Buybacks
        full_equity = last_equity + divs_paid + repurchased_net
        
        # Variant 2: Full Equity (With Debt Adjustment)
        # Offset buybacks/dividends funded by debt
        initial_debt = df['total_debt'].iloc[0]
        last_debt = df['total_debt'].iloc[-1]
        debt_change = last_debt - initial_debt
        
        # Only offset the portion of distributions (divs + net buybacks) that can be attributed to debt increase
        distributions = divs_paid + repurchased_net
        debt_offset = min(max(0.0, debt_change), distributions)
        full_equity_with_debt = full_equity - debt_offset
        
        # Variant 3: Full Equity (Retained Earnings / Net Income based)
        total_net_income = df['net_income'].sum()
        full_equity_ni = initial_equity + total_net_income
        
        # Calculate CAGRs
        def cagr(final, initial, years):
            if initial <= 0 or final <= 0:
                return 0.0
            return (final / initial) ** (1 / years) - 1

        return {
            "CAGR Full Equity (%)": cagr(full_equity, initial_equity, years_elapsed) * 100,
            "CAGR Full Equity w/ Debt (%)": cagr(full_equity_with_debt, initial_equity, years_elapsed) * 100,
            "CAGR Full Equity NI (%)": cagr(full_equity_ni, initial_equity, years_elapsed) * 100,
            "Years Analyzed": round(years_elapsed, 1),
            "Initial Equity": initial_equity,
            "Last Equity": last_equity,
            "Total cum. Dividends Paid": divs_paid,
            "Total cum. Net Repurchases": repurchased_net,
            "Total cum. Debt Change": debt_change,
            "Total cum. Net Income": total_net_income
        }

