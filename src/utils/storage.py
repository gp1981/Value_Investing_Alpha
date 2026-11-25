"""
Canonical storage & path resolution utilities for Value Investing Alpha.

Provides resilient fallback from external bulk storage (e.g. /Volumes/T3/edgartools)
to local repo output/ directories when external drives are disconnected,
and centralizes paths for company_data.csv, users.json, and edgar cache.
"""

import logging
import os
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
DEFAULT_OUTPUT_DIR = os.path.join(_REPO_ROOT, "output")


def is_path_available(path: str) -> bool:
    """
    Return True if `path` exists and is writable, or can be safely created
    without attempting to create an unmounted volume root (e.g. /Volumes/T3).
    """
    if not path:
        return False
    abs_path = os.path.abspath(path)
    if os.path.exists(abs_path):
        return os.access(abs_path, os.W_OK)

    cur = abs_path
    while cur and not os.path.exists(cur):
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent

    # Never attempt to mkdir directly under / or external mount roots
    if cur in ("/", "/Volumes", "/mnt", "/media"):
        return False
    return os.access(cur, os.W_OK)


def resolve_edgar_paths(
    preferred_data_dir: Optional[str] = None,
    preferred_cache_dir: Optional[str] = None,
) -> Tuple[str, str, bool]:
    """
    Resolve (edgar_data_dir, edgar_cache_dir, using_external_storage).

    If `preferred_data_dir` (e.g. /Volumes/T3/edgartools) is mounted and accessible,
    returns its data & cache subdirectories without double-nesting `/data/data`.
    Otherwise, gracefully falls back to `output/edgar_data` and `output/edgar_cache`.
    """
    env_data = preferred_data_dir or os.getenv("EDGAR_LOCAL_DATA_DIR")
    env_cache = preferred_cache_dir or (None if preferred_data_dir else os.getenv("EDGAR_CACHE_DIR"))

    using_external = False
    data_dir = None
    cache_dir = None

    if env_data and is_path_available(env_data):
        clean = os.path.abspath(env_data).rstrip("/")
        if os.path.basename(clean) == "data":
            data_dir = clean
            cache_dir = os.path.join(os.path.dirname(clean), "cache")
        else:
            data_dir = os.path.join(clean, "data") if os.path.exists(os.path.join(clean, "data")) or not os.path.exists(clean) else clean
            cache_dir = os.path.join(clean, "cache")
        using_external = True
    else:
        if env_data:
            logger.warning(
                f"Configured EDGAR_LOCAL_DATA_DIR '{env_data}' is not mounted or writable. "
                f"Falling back to local '{DEFAULT_OUTPUT_DIR}/edgar_data' + live SEC queries."
            )
        data_dir = os.path.join(DEFAULT_OUTPUT_DIR, "edgar_data")
        cache_dir = os.path.join(DEFAULT_OUTPUT_DIR, "edgar_cache")

    if env_cache and is_path_available(env_cache):
        cache_dir = os.path.abspath(env_cache)

    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(cache_dir, exist_ok=True)
    return data_dir, cache_dir, using_external


def get_company_data_csv() -> str:
    """Return the canonical path to company_data.csv, checking standard locations."""
    candidates = [
        os.path.join(DEFAULT_OUTPUT_DIR, "company_data.csv"),
        "output/company_data.csv",
        "output/data/data/company_data.csv",
        "output/data/company_data.csv",
    ]
    for path in candidates:
        if os.path.exists(path) and os.path.getsize(path) > 100:
            return path
    return os.path.join(DEFAULT_OUTPUT_DIR, "company_data.csv")


def get_users_file() -> str:
    """Return canonical path for local users.json inside output/."""
    os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)
    return os.path.join(DEFAULT_OUTPUT_DIR, "users.json")
