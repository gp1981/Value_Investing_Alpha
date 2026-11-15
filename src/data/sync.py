import os
import argparse
import logging

def sync_sec_data(identity: str, storage_dir: str):
    """
    Standalone function to bulk download SEC data to a local directory.
    Follows the logic provided by the user to ensure data and cache are external.
    """
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logger = logging.getLogger("SEC-Sync")

    # 1. Define paths
    data_dir = os.path.join(storage_dir, "data")
    cache_dir = os.path.join(storage_dir, "cache")

    # 2. Create directories
    logger.info(f"Preparing storage at: {storage_dir}")
    for path in [data_dir, cache_dir]:
        os.makedirs(path, exist_ok=True)

    # 3. Force external paths via environment variables BEFORE importing edgar
    os.environ['EDGAR_LOCAL_DATA_DIR'] = data_dir
    os.environ['EDGAR_CACHE_DIR'] = cache_dir
    
    # 4. Lazy import edgar after env vars are set
    try:
        from edgar.settings import set_identity
    except ImportError:
        from edgar import set_identity
    from edgar import use_local_storage, download_edgar_data

    # 5. Configure Identity
    set_identity(identity)
    
    # 6. Initialize local storage
    use_local_storage(data_dir)

    # 7. Run Bulk Download
    logger.info(f"Starting bulk download to: {data_dir}")
    logger.info("This may take a while (approx. 24GB)...")
    
    try:
        download_edgar_data()
        logger.info("Successfully synchronized SEC data!")
    except PermissionError as e:
        logger.error(f"Permission Error: {e}. Try running with appropriate permissions or check directory access.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Standalone SEC EDGAR Data Synchronizer")
    parser.add_argument("--identity", default="Value Investing Screener screener@example.com", help="SEC User-Agent identity")
    parser.add_argument("--storage", default="/Volumes/T3/edgartools", help="Root directory for local SEC storage")
    
    args = parser.parse_args()
    sync_sec_data(args.identity, args.storage)
