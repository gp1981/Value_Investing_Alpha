import os
import pytest

def test_edgartools_version():
    import edgar
    from packaging.version import Version
    assert Version(edgar.__version__) >= Version("5.56.0")

def test_edgar_settings_import():
    try:
        from edgar.settings import set_identity, get_identity, get_edgar_data_directory
        assert callable(set_identity)
        assert callable(get_identity)
    except ImportError:
        pytest.fail("Failed to import from edgar.settings")

def test_sync_sec_data_uses_supported_edgartools_api(tmp_path, monkeypatch):
    monkeypatch.setenv("EDGAR_LOCAL_DATA_DIR", str(tmp_path / "initial-data"))
    monkeypatch.setenv("EDGAR_CACHE_DIR", str(tmp_path / "initial-cache"))

    import edgar
    from src.data.sync import sync_sec_data

    downloads = []
    monkeypatch.setattr(edgar, "download_edgar_data", lambda: downloads.append(True))

    sync_sec_data("Test App test@example.com", str(tmp_path))

    assert downloads == [True]
    assert os.environ["EDGAR_LOCAL_DATA_DIR"] == os.path.join(tmp_path, "data")
    assert os.environ["EDGAR_CACHE_DIR"] == os.path.join(tmp_path, "cache")

def test_sec_provider_initialization_uses_supported_edgartools_api(tmp_path, monkeypatch):
    monkeypatch.setenv("EDGAR_LOCAL_DATA_DIR", str(tmp_path / "initial-data"))
    monkeypatch.setenv("EDGAR_CACHE_DIR", str(tmp_path / "initial-cache"))

    from src.data.sec_provider import SECProvider

    storage_dir = tmp_path / "provider"
    SECProvider(storage_dir=str(storage_dir))

    assert os.environ["EDGAR_LOCAL_DATA_DIR"] == os.path.join(storage_dir, "data")
    assert os.environ["EDGAR_CACHE_DIR"] == os.path.join(storage_dir, "cache")

def test_sec_provider_initialization():
    storage = "/Volumes/T3/edgartools"
    if not os.path.exists(storage):
        pytest.skip(f"External storage {storage} not connected")
        
    from src.data.sec_provider import SECProvider
    provider = SECProvider(storage_dir=storage)
    assert provider.is_storage_populated() is True

def test_entity_facts_local_retrieval():
    storage = "/Volumes/T3/edgartools"
    if not os.path.exists(storage):
        pytest.skip(f"External storage {storage} not connected")
        
    os.environ['EDGAR_LOCAL_DATA_DIR'] = os.path.join(storage, "data")
    os.environ['EDGAR_CACHE_DIR'] = os.path.join(storage, "cache")
    
    from edgar import Company, use_local_storage
    from edgar.settings import set_identity
    
    set_identity("Value Investing Screener screener@example.com")
    use_local_storage(os.path.join(storage, "data"))
    
    c = Company("AAPL")
    assert c.name == "Apple Inc."
    assert hasattr(c, "facts")
    
    facts = c.facts
    assert facts is not None
    
    # Test balance sheet retrieval from local facts
    bs = facts.balance_sheet()
    assert bs is not None
    df_bs = bs.to_dataframe()
    assert not df_bs.empty
    assert "label" in df_bs.columns or "concept" in df_bs.columns
