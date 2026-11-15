import pandas as pd

def format_currency(value) -> str:
    """Format large numbers into human-readable currency strings (e.g., $1.23B, $450.00M)."""
    try:
        val = float(value)
        if pd.isna(val):
            return "N/A"
        abs_val = abs(val)
        if abs_val >= 1e9:
            return f"${val / 1e9:,.2f}B"
        elif abs_val >= 1e6:
            return f"${val / 1e6:,.2f}M"
        else:
            return f"${val:,.0f}"
    except (ValueError, TypeError):
        return str(value)
