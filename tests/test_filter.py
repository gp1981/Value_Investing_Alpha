import pytest
import pandas as pd
from unittest.mock import MagicMock
from src.engine.filter import CompanyFilter

def test_apply_foreign_filter():
    market_mock = MagicMock()
    sec_mock = MagicMock()
    cf = CompanyFilter(market_mock, sec_mock)
    
    df = pd.DataFrame({
        "ticker": ["AAPL", "BABA", "MSFT", "ASML"]
    })
    
    filtered = cf.apply_foreign_filter(df)
    valid_tickers = filtered["ticker"].tolist()
    
    assert "AAPL" in valid_tickers
    assert "MSFT" in valid_tickers
    assert "BABA" not in valid_tickers
    assert "ASML" not in valid_tickers

def test_apply_industry_filters():
    market_mock = MagicMock()
    sec_mock = MagicMock()
    cf = CompanyFilter(market_mock, sec_mock)
    
    df = pd.DataFrame({
        "ticker": ["AAPL", "JPM", "MSFT", "BAC"],
        "sic": [3571, 6021, 7372, 6022]  # JPM and BAC are banks in 6000-6999
    })
    
    filtered = cf.apply_industry_filters(df)
    remaining_tickers = filtered["ticker"].tolist()
    
    assert "AAPL" in remaining_tickers
    assert "MSFT" in remaining_tickers
    assert "JPM" not in remaining_tickers
    assert "BAC" not in remaining_tickers
