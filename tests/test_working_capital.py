import os
import pytest
from src.models.safety import SafetyModel

def test_working_capital_anomaly_normal():
    safety = SafetyModel()
    # Revenue +10%, AR +10%, Inventory +8% -> Normal
    res = safety.calculate_working_capital_anomaly(
        current_rev=110.0, prev_rev=100.0,
        current_ar=22.0, prev_ar=20.0,
        current_inv=16.2, prev_inv=15.0
    )
    assert res["wc_anomaly_signal"] == "NORMAL"
    assert res["rev_growth"] == 10.0
    assert res["ar_growth"] == 10.0
    assert res["ar_divergence"] == 0.0

def test_working_capital_anomaly_ar_warning():
    safety = SafetyModel()
    # Revenue +5%, AR +25% -> Divergence = +20% (>15% warning threshold)
    res = safety.calculate_working_capital_anomaly(
        current_rev=105.0, prev_rev=100.0,
        current_ar=25.0, prev_ar=20.0,
        current_inv=15.0, prev_inv=15.0
    )
    assert res["wc_anomaly_signal"] == "WARNING"
    assert res["ar_growth"] == 25.0
    assert res["ar_divergence"] == 20.0

def test_working_capital_anomaly_inv_warning():
    safety = SafetyModel()
    # Revenue +5%, Inventory +25% -> Divergence = +20% (>15% warning threshold)
    res = safety.calculate_working_capital_anomaly(
        current_rev=105.0, prev_rev=100.0,
        current_ar=21.0, prev_ar=20.0,
        current_inv=18.75, prev_inv=15.0
    )
    assert res["wc_anomaly_signal"] == "WARNING"
    assert res["inv_divergence"] == 20.0

def test_working_capital_anomaly_elevated():
    safety = SafetyModel()
    # Revenue +5%, AR +17% -> Divergence = +12% (10%-15% elevated threshold)
    res = safety.calculate_working_capital_anomaly(
        current_rev=105.0, prev_rev=100.0,
        current_ar=23.4, prev_ar=20.0,
        current_inv=15.0, prev_inv=15.0
    )
    assert res["wc_anomaly_signal"] == "ELEVATED"
    assert res["ar_divergence"] == 12.0

def test_working_capital_anomaly_service_company_no_inventory():
    safety = SafetyModel()
    # No inventory: Revenue +10%, AR +12% -> Normal
    res = safety.calculate_working_capital_anomaly(
        current_rev=110.0, prev_rev=100.0,
        current_ar=22.4, prev_ar=20.0,
        current_inv=0.0, prev_inv=0.0
    )
    assert res["wc_anomaly_signal"] == "NORMAL"
    assert res["inv_growth"] == 0.0
    assert res["inv_divergence"] == 0.0

def test_working_capital_anomaly_invalid_baseline():
    safety = SafetyModel()
    # Missing baseline revenue
    res = safety.calculate_working_capital_anomaly(
        current_rev=100.0, prev_rev=0.0,
        current_ar=20.0, prev_ar=20.0
    )
    assert res["wc_anomaly_signal"] == "N/A"

def test_working_capital_real_extraction():
    storage = "/Volumes/T3/edgartools"
    if not os.path.exists(storage):
        pytest.skip(f"External storage {storage} not connected")
    
    from src.data.sec_provider import SECProvider
    sec = SECProvider(storage_dir=storage)
    
    # Test AAPL fast extraction
    wc = sec.get_working_capital_metrics("AAPL")
    assert wc["current_rev"] > 0
    assert wc["prev_rev"] > 0
    assert wc["current_ar"] > 0
    assert wc["prev_ar"] > 0
    
    # Test financial statement integration
    fs = sec.get_financials("AAPL", enrich=True)
    assert fs.wc_anomaly_signal in {"NORMAL", "ELEVATED", "WARNING"}
    assert fs.prev_revenue > 0
