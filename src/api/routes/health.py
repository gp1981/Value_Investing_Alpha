from fastapi import APIRouter
import sys
import os

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("")
def health_check():
    """System health check and runtime status."""
    return {
        "status": "healthy",
        "service": "Value Investing Alpha API",
        "python_version": sys.version.split(" ")[0],
        "sec_identity_set": bool(os.getenv("EDGAR_IDENTITY")),
        "cache_dir_set": bool(os.getenv("EDGAR_LOCAL_DATA_DIR"))
    }
