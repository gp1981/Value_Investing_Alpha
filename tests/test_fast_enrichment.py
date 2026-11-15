import os
import pytest
import pandas as pd

@pytest.fixture
def sec_provider():
    storage = "/Volumes/T3/edgartools"
    if not os.path.exists(storage):
        pytest.skip(f"External storage {storage} not connected")
    from src.data.sec_provider import SECProvider
    return SECProvider(storage_dir=storage)

def test_fast_revenue_history_and_description(sec_provider):
    fs = sec_provider.get_financials("AAPL", enrich=True)
    assert fs is not None
    assert fs.revenue_history is not None
    assert len(fs.revenue_history) >= 4
    # Check that keys are in sortable format
    keys = sorted(fs.revenue_history.keys(), reverse=True)
    assert len(keys) >= 4
    # Check description
    assert fs.description is not None
    assert len(fs.description) > 20
    assert "business" in fs.description.lower() or "apple" in fs.description.lower()

def test_fast_historical_data(sec_provider):
    hist = sec_provider.get_historical_data("AAPL", max_years=5)
    assert not hist.empty
    assert len(hist) >= 4
    expected_cols = {"date", "equity", "net_income", "dividends", "repurchases", "issuances", "total_debt"}
    assert expected_cols.issubset(set(hist.columns))
    
    # Check equity analysis calculation
    from src.models.equity_analysis import EquityAnalysisModel
    model = EquityAnalysisModel()
    metrics = model.calculate_metrics(hist)
    assert "CAGR Full Equity (%)" in metrics
    assert metrics["CAGR Full Equity (%)"] > 0
    assert "Years Analyzed" in metrics

def test_sec_provider_clear_cache(sec_provider):
    # Ensure clear_cache executes cleanly with company facts cache
    sec_provider.clear_cache()
