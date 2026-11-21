from fastapi import APIRouter
import sys
import os
import pandas as pd

router = APIRouter(prefix="/health", tags=["Health"])

def get_cache_file() -> str:
    candidates = [
        "output/company_data.csv",
        "output/data/data/company_data.csv",
        "output/data/company_data.csv"
    ]
    for path in candidates:
        if os.path.exists(path) and os.path.getsize(path) > 100:
            return path
    return "output/company_data.csv"

@router.get("")
def health_check():
    """System health check and runtime status (for Cloud Run probes)."""
    return {
        "status": "healthy",
        "service": "Value Investing Alpha API",
        "python_version": sys.version.split(" ")[0],
        "sec_identity_set": bool(os.getenv("EDGAR_IDENTITY")),
        "cache_dir_set": bool(os.getenv("EDGAR_LOCAL_DATA_DIR"))
    }

@router.get("/storage")
def storage_status():
    """Detailed cache and local storage telemetry for UI status indicators."""
    storage_dir = os.getenv("EDGAR_LOCAL_DATA_DIR", "output")
    cache_path = get_cache_file()
    cache_exists = os.path.exists(cache_path)
    cached_count = 0
    file_size_kb = 0

    if cache_exists:
        try:
            file_size_kb = round(os.path.getsize(cache_path) / 1024, 1)
            df = pd.read_csv(cache_path)
            cached_count = len(df)
        except Exception:
            pass

    return {
        "status": "online",
        "storage_dir": storage_dir,
        "cache_file": cache_path,
        "cache_exists": cache_exists,
        "cached_tickers_count": cached_count,
        "cache_size_kb": file_size_kb,
        "sec_identity": os.getenv("EDGAR_IDENTITY", "Default configured")
    }
