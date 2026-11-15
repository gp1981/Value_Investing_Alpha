from src.data import exceptions
from ..data.schemas import FinancialStatement, MarketData

class MagicFormulaModel:
    """
    Implements Joel Greenblatt's Magic Formula with refined Excess Cash estimation.
    Ranking criteria:
    1. Earnings Yield = EBIT / Enterprise Value
    2. Return on Capital = EBIT / Tangible Capital Employed
    """
    
    def calculate_excess_cash(self, fs: FinancialStatement, industry_median_ratio: float = 0.0) -> float:
        """
        Estimate excess cash not needed for operations.
        Operating Cash = Median(Industry Cash/Revenue) * Revenue
        Excess Cash = Total Cash - Operating Cash
        
        Note: If industry_median_ratio is 0, we assume all cash is excess (original formula).
        """
        operating_cash_needed = (industry_median_ratio or 0) * (fs.revenue or 0)
        excess_cash = (fs.cash_and_equivalents or 0) - operating_cash_needed
        return max(0.0, excess_cash)

    def calculate_earnings_yield(self, fs: FinancialStatement, md: MarketData, industry_median_ratio: float = 0.0) -> float:
        """
        EY = EBIT / Enterprise Value
        EV = Market Cap + Total Debt - Excess Cash
        """
        total_debt = (fs.short_term_debt or 0) + (fs.long_term_debt or 0)
        excess_cash = self.calculate_excess_cash(fs, industry_median_ratio) # Not used in the below calculation
        
        # ev = (md.market_cap or 0) + total_debt - excess_cash
        ev = (md.market_cap or 0) + total_debt - fs.cash_and_equivalents

        # Condition 1: If EBIT is zero or negative, return 0
        if fs.ebit <= 0:
            return 0.0

        # Condition 2: If EV is zero or negative, fallback to Market Cap
        if ev <= 0:
            # Added a check to prevent ZeroDivisionError just in case market_cap is 0
            return fs.ebit / md.market_cap if md.market_cap else 0.0

        # Default: Standard Earnings Yield calculation
        return fs.ebit / ev
        
    def calculate_tangible_capital_employed(self, fs: FinancialStatement, industry_median_ratio: float = 0.0) -> float:
        """
        Tangible Capital Employed = Total Assets - Goodwill/Intangibles - Cash
        
        """
        total_debt = (fs.short_term_debt or 0) + (fs.long_term_debt or 0)
        nibl = (fs.total_liabilities or 0) - total_debt
        
        excess_cash = self.calculate_excess_cash(fs, industry_median_ratio) # Not used in the below calculation
        
        tangible_capital = (fs.total_assets or 0) - (fs.goodwill_and_intangible_assets or 0) - fs.cash_and_equivalents

        if tangible_capital <= 0:
            # return positive value if negative tangible capital
            return 1000
        
        return tangible_capital

    def calculate_roc(self, fs: FinancialStatement, md: MarketData, industry_median_ratio: float = 0.0) -> float:
        """
        ROC = EBIT / Tangible Capital Employed
        """
        tangible_capital = self.calculate_tangible_capital_employed(fs, industry_median_ratio)

        if tangible_capital <= 0:
            return 1000.0 # Extremely high ROC for negative capital
        
        return fs.ebit / tangible_capital
