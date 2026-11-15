from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from src.api.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    if "text/html" in response.headers.get("content-type", ""):
        assert "<!doctype html>" in response.text.lower()
    else:
        data = response.json()
        assert data["status"] == "operational"


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "python_version" in data

def test_screener_results_endpoint():
    response = client.get("/api/screener/results?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total_count" in data
    assert len(data["items"]) > 0
    first_item = data["items"][0]
    assert "ticker" in first_item
    assert "ebit" in first_item
    assert "earnings_yield" in first_item
    assert "return_on_capital" in first_item

def test_screener_results_sorting():
    response = client.get("/api/screener/results?sort_by=market_cap&sort_order=desc&limit=3")
    assert response.status_code == 200
    data = response.json()
    items = data["items"]
    assert len(items) >= 2
    # Ensure descending order
    assert items[0]["market_cap"] >= items[1]["market_cap"]

def test_screener_run_endpoint():
    payload = {
        "tickers": ["AAPL", "MSFT"],
        "min_market_cap": 10000000,
        "limit": 10
    }
    response = client.post("/api/screener/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) > 0

def test_company_details_demo_endpoint():
    response = client.get("/api/company/AAPL")
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "AAPL"
    assert "magic_formula" in data
    assert "greenwald" in data
    assert "dcf" in data
    assert "safety" in data
    assert "financial_statement" in data
    assert data["magic_formula"]["earnings_yield"] > 0
    assert data["greenwald"]["reproduction_value"] > 0
    assert data["safety"]["traffic_light"] in ["GREEN", "YELLOW", "RED"]

def test_company_details_404():
    with patch("src.engine.integrator.DataIntegrator.fetch_company_data", side_effect=Exception("Ticker not found")):
        response = client.get("/api/company/INVALID_TICKER_XYZ999")
        assert response.status_code == 404

