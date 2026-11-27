from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from datetime import datetime
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

def test_storage_health():
    response = client.get("/health/storage")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "storage_dir" in data

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

def test_screener_export_csv():
    response = client.get("/api/screener/export/csv?limit=5")
    assert response.status_code == 200
    assert "text/csv" in response.headers.get("content-type", "")
    assert "ticker" in response.text
    assert len(response.text.splitlines()) >= 2

def test_screener_export_excel():
    response = client.get("/api/screener/export/excel?limit=5")
    assert response.status_code == 200
    assert "spreadsheetml" in response.headers.get("content-type", "")
    assert len(response.content) > 100

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


def test_auth_login_default_user():
    response = client.post("/api/auth/login", json={
        "email": "analyst@example.com",
        "password": "valuealpha2026"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "analyst@example.com"
    assert data["user"]["tier"] == "FREE"

def test_auth_login_invalid_password():
    response = client.post("/api/auth/login", json={
        "email": "analyst@example.com",
        "password": "wrongpassword123"
    })
    assert response.status_code == 401

def test_auth_register_and_me():
    new_email = f"test_{int(datetime.now().timestamp())}@example.com"
    reg_response = client.post("/api/auth/register", json={
        "email": new_email,
        "password": "securepassword123",
        "full_name": "Test Trader"
    })
    assert reg_response.status_code == 200
    token = reg_response.json()["access_token"]

    # Test /api/auth/me with bearer token
    me_response = client.get("/api/auth/me", headers={
        "Authorization": f"Bearer {token}"
    })
    assert me_response.status_code == 200
    user_data = me_response.json()
    assert user_data["email"] == new_email
    assert user_data["full_name"] == "Test Trader"

def test_auth_me_unauthorized():
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_storage_fallback_when_unmounted():
    from src.utils.storage import resolve_edgar_paths, is_path_available
    assert is_path_available("/Volumes/NON_EXISTENT_VOLUME_XYZ/edgartools") is False
    data_dir, cache_dir, using_ext = resolve_edgar_paths("/Volumes/NON_EXISTENT_VOLUME_XYZ/edgartools")
    assert using_ext is False
    assert data_dir.endswith("output/edgar_data")
    assert cache_dir.endswith("output/edgar_cache")


def test_edgar_forms_catalog():
    response = client.get("/api/company/edgar-forms")
    assert response.status_code == 200
    forms = response.json().get("forms", [])
    form_codes = [f["form"] for f in forms]
    assert "10-K" in form_codes
    assert "10-Q" in form_codes
    assert "8-K" in form_codes
    assert "13F-HR" in form_codes


def test_superinvestors_list():
    response = client.get("/api/superinvestors/list")
    assert response.status_code == 200
    investors = response.json()
    assert len(investors) >= 10
    ciks = [i["cik"] for i in investors]
    assert "0001067983" in ciks  # Berkshire Hathaway / Warren Buffett


def test_is_storage_populated_ignores_tcache(tmp_path):
    from src.data.sec_provider import SECProvider
    data_dir = tmp_path / "data"
    (data_dir / "_tcache").mkdir(parents=True)
    (data_dir / "_tcache" / "dummy.db").write_text("x")
    sp = SECProvider(storage_dir=str(tmp_path))
    assert sp.is_storage_populated() is False


def test_fcff_and_roic_horizon_computation():
    from src.engine.horizon_metrics import compute_company_horizon_metrics
    fs_dict = {
        "ebit": 1000.0,
        "operating_cash_flow": 1200.0,
        "capex": 200.0,
        "interest_expense_ttm": 50.0,
        "income_tax_expense_ttm": 200.0,
        "inventory": 300.0,
        "accounts_receivable": 200.0,
        "accounts_payable": 100.0,
        "net_fixed_assets": 1600.0,
    }
    fcff_ttm, mc_to_fcff_ttm, _, _, horizons = compute_company_horizon_metrics("AAPL_TEST_OFFLINE", fs_dict, 10000.0)
    assert fcff_ttm is not None and fcff_ttm > 0
    assert mc_to_fcff_ttm is not None and mc_to_fcff_ttm > 0
    assert len(horizons) == 4
    assert horizons[0]["horizon"] == "TTM"
    assert horizons[0]["roic_pct"] is not None and horizons[0]["roic_pct"] > 0
