from ..data.schemas import FinancialStatement, MarketData

class DCFModel:
    """
    Implements a steady-state Discounted Cash Flow (DCF) model.
    Applicable for businesses with low FCF volatility.
    """
    
    def calculate_intrinsic_value(self, fs: FinancialStatement, discount_rate: float, growth_rate: float = 0.02) -> float:
        """
        Intrinsic Value = FCF * (1 + g) / (r - g)
        FCF = Cash Flow from Operations - Maintenance CapEx
        For MVP: We'll use (Net Income + D&A - CapEx) as proxy for FCF if not directly available.
        """
        # Calculate FCF Proxy
        # If D&A or CapEx are 0 (missing data), use Net Income as conservative floor
        fcf = fs.net_income + fs.depreciation_amortization - fs.capex
        
        if fcf <= 0:
            return 0.0
            
        if discount_rate <= growth_rate:
            return 0.0
            
        terminal_value = fcf * (1 + growth_rate) / (discount_rate - growth_rate)
        return terminal_value
