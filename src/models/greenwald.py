from ..data.schemas import FinancialStatement, MarketData

class GreenwaldModel:
    """
    Implements Bruce Greenwald's Value Investing framework.
    1. Asset Reproduction Value (Adjusted Balance Sheet)
    2. Earning Power Value (EPV) = Normalized Earnings / WACC
    """
    
    def calculate_reproduction_value(self, fs: FinancialStatement) -> float:
        """
        Estimate the cost to reproduce the company's assets.
        Simplified version: Total Assets - Excess Cash - Non-operating assets + adjustments.
        For MVP: Net Assets (Total Assets - Total Liabilities) or Book Value.
        Actually Greenwald focuses on adjusting specific items like AR, Inventory, PPE.
        """
        # Simplified Greenwald Reproduction Value
        # Adjustments would normally be:
        # AR: 100%, Inventory: 100%, PPE: 100% (or replacement cost)
        # We'll use a conservative approximation for now.
        total_liabilities = fs.total_assets - (fs.total_assets - fs.current_liabilities - fs.long_term_debt) # Approximation
        # Let's just use: Total Assets - (Total Liabilities - Total Debt) -> Book Value + Debt
        # More accurate for reproduction: Adjusted Assets - Current Liabilities (non-debt)
        
        non_interest_bearing_cl = fs.current_liabilities - fs.short_term_debt
        reproduction_value = fs.total_assets - non_interest_bearing_cl
        
        return reproduction_value

    def calculate_epv(self, fs: FinancialStatement, wacc: float = 0.10) -> float:
        """
        EPV = Adjusted EBIT * (1 - TaxRate) / WACC
        For steady state: No growth assumed.
        """
        # Normalized EBIT: For MVP we use current EBIT
        # Standard tax rate: 25%
        tax_rate = 0.25
        normalized_earnings = fs.ebit * (1 - tax_rate)
        
        if wacc <= 0:
            return 0.0
            
        return normalized_earnings / wacc
