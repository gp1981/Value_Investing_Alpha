import argparse
import sys
import logging
import os
import pandas as pd
from tabulate import tabulate

def setup_logging(output_dir="output"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    log_file = os.path.join(output_dir, "screener.log")
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Clean old handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # File handler (all logs including warnings)
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.WARNING)
    fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    root_logger.addHandler(fh)
    
    # stdout handler (INFO only for clean display)
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    # Filter out warnings from stdout
    sh.addFilter(lambda record: record.levelno <= logging.INFO)
    sh.setFormatter(logging.Formatter('%(message)s'))
    root_logger.addHandler(sh)

def main():
    parser = argparse.ArgumentParser(description="Value Investing Screener (SEC & Market Data)")
    parser.add_argument("--tickers", nargs="+", help="Optional list of stock tickers to screen. If omitted, uses the full SEC universe.")
    parser.add_argument("--sort", choices=["magic", "epv", "dcf"], default="magic", help="Criteria to sort by")
    parser.add_argument("--identity", default="Value Investing Screener screener@example.com", help="SEC User-Agent identity")
    parser.add_argument("--storage", default="/Volumes/T3/edgartools", help="edgartools local storage directory")
    parser.add_argument("--limit", type=int, help="Limit the number of tickers to process (for testing)")
    parser.add_argument("--benchmark", action="store_true", help="Run benchmark comparison with magicformulainvesting.com")
    parser.add_argument("--thresholds", type=int, nargs="+", default=list(range(100, 2000, 100)), help="Space-separated list of market cap thresholds (in millions) for benchmarking")
    parser.add_argument("--refresh", action="store_true", help="Force refresh of cached universe and benchmark data")
    parser.add_argument("--cache-only", action="store_true", help="Run screening and benchmark ONLY using data already in output/company_data.csv")
    parser.add_argument("--sync-storage", action="store_true", help="Bulk download EDGAR data to local storage directory")
    parser.add_argument("--enrich", action="store_true", help="Enrich data with company descriptions and revenue history (slower)")
    parser.add_argument("--mktcap", type=float, help="Minimum market cap threshold in millions USD (mUSD)")
    
    args = parser.parse_args()

    # Calculate market cap threshold in absolute USD (mUSD -> USD)
    min_mkt_cap_usd = args.mktcap * 1_000_000 if args.mktcap else 0
    
    # CRITICAL: Set environment variables before any edgartools imports.
    # This ensures that all internal caches (like _tcache) are directed to the external drive.
    os.environ['EDGAR_LOCAL_DATA_DIR'] = os.path.join(args.storage, "data")
    os.environ['EDGAR_CACHE_DIR'] = os.path.join(args.storage, "cache")
    
    # Lazy imports after environment setup
    from src.data.sec_provider import SECProvider
    from src.data.market_provider import MarketDataProvider
    from src.engine.integrator import DataIntegrator
    from src.engine.screener import Screener
    from src.engine.filter import CompanyFilter
    
    setup_logging()
    logger = logging.getLogger("Main")
    
    try:
        # Initialize components
        sec = SECProvider(identity=args.identity, storage_dir=args.storage)
        
        # Check if we should sync storage
        if args.sync_storage:
            sec.sync_storage()
            return
            
        if not sec.is_storage_populated() and not args.cache_only:
            logger.info("\n" + "!"*80)
            logger.info("SEC local storage appears to be empty.")
            logger.info(f"Target directory: {args.storage}")
            logger.info("Running without local data will be significantly slower as it fetches company-by-company.")
            logger.info("To perform a bulk download (approx. 24GB), run with the --sync-storage flag.")
            logger.info("!"*80 + "\n")

        market = MarketDataProvider()
        integrator = DataIntegrator(sec, market)
        screener = Screener(integrator)
        
        tickers = args.tickers
        company_filter = CompanyFilter(market, sec)

        if not tickers:
            # Incremental Mode: Prioritize cached data for benchmarking
            cached_data_path = "output/company_data.csv"
            benchmark_mf_path = "output/benchmark_mf.csv"
            
            if args.cache_only:
                if os.path.exists(cached_data_path):
                    cd_df = pd.read_csv(cached_data_path)
                    tickers = cd_df['ticker'].dropna().unique().tolist()
                    logger.info(f"Cache-only mode: Using {len(tickers)} tickers from {cached_data_path}")
                else:
                    logger.error(f"Cache-only mode requested but {cached_data_path} not found.")
                    return

            elif args.benchmark and not args.refresh:
                cached_tickers = []
                if os.path.exists(cached_data_path):
                    try:
                        cd_df = pd.read_csv(cached_data_path)
                        if 'ticker' in cd_df.columns:
                            cached_tickers = cd_df['ticker'].dropna().unique().tolist()
                    except Exception as e:
                        logger.warning(f"Could not load cached tickers: {str(e)}")
                
                bm_tickers = []
                if os.path.exists(benchmark_mf_path):
                    try:
                        bm_df = pd.read_csv(benchmark_mf_path)
                        if 'Ticker' in bm_df.columns:
                            bm_tickers = bm_df['Ticker'].dropna().unique().tolist()
                    except Exception as e:
                        logger.warning(f"Could not load benchmark tickers: {str(e)}")
                
                if cached_tickers or bm_tickers:
                    tickers = list(set(cached_tickers) | set(bm_tickers))
                    logger.info(f"Incremental mode: Using {len(cached_tickers)} cached tickers and {len(bm_tickers)} benchmark tickers. Total: {len(tickers)}")
            
            if not tickers:
                universe_path = "output/universe.csv"
                if os.path.exists(universe_path) and not args.refresh:
                    logger.info(f"Loading stock universe from {universe_path}...")
                    universe_df = pd.read_csv(universe_path)
                else:
                    logger.info("No tickers provided or refresh forced. Retrieving universe from SEC...")
                    universe_df = company_filter.get_candidate_companies()
                    universe_df.to_csv(universe_path, index=False)
                    logger.info(f"Full universe ({len(universe_df)} stocks) saved to {universe_path}")
                
                # Apply initial filters (SIC, ADR)
                logger.info("Applying initial filters (SIC exclusions)...")
                filtered_df = company_filter.apply_industry_filters(universe_df)
                tickers = filtered_df['ticker'].dropna().unique().tolist()
        else:
            # If explicit tickers, still filter them by SIC
            # We need a small df to use the filter
            df = pd.DataFrame({'ticker': tickers})
            filtered_df = company_filter.apply_industry_filters(df)
            tickers = filtered_df['ticker'].dropna().unique().tolist()
            
        if args.limit:
            tickers = tickers[:args.limit]
            
        # Run screening
        logger.info(f"Starting screening for {len(tickers)} tickers...")
        df = screener.screen_tickers(tickers, enrich=args.enrich)
        
        if df.empty:
            logger.error("No data retrieved for any of the tickers.")
            return

        # Benchmark Comparison
        if args.benchmark:
            df = screener.run_benchmark_comparison(df, thresholds=args.thresholds, force_refresh=args.refresh)

        # Sort and Format
        if args.sort == "magic":
            df = df.sort_values("Magic Rank")
        elif args.sort == "epv":
            df = df.sort_values("EPV/MC", ascending=False)
        elif args.sort == "dcf":
            df = df.sort_values("DCF/MC", ascending=False)

        # Apply final market cap filter if requested
        if min_mkt_cap_usd > 0:
            count_before = len(df)
            df = df[df['market_cap'] >= min_mkt_cap_usd]
            logger.info(f"Market cap filter (>= ${args.mktcap}M): {len(df)} companies remaining (filtered out {count_before - len(df)})")
            
        # Display
        display_cols = ["Ticker", "price", "EY (%)", "ROC (%)", "Magic Rank", "sic_code", "Industry Ratio"]
        
        if "EPV/MC" in df.columns: display_cols.append("EPV/MC")
        if "DCF/MC" in df.columns: display_cols.append("DCF/MC")

        # Rename for prettier display
        rename_map = {
            "price": "Price",
            "sic_code": "SIC",
            "Industry Ratio": "Ind. Ratio"
        }
        
        print("\n" + "="*100)
        print("VALUE INVESTING SCREENER RESULTS")
        print("="*100)
        print(tabulate(df[display_cols].head(50).rename(columns=rename_map), headers='keys', tablefmt='psql', showindex=False))
        print("="*100)
        print(f"\nSorting criteria: {args.sort.upper()}")
        print(f"Total companies screened: {len(df)}")
        print(f"Logs saved to output/screener.log")
        print(f"Aggregated data saved to output/company_data.csv")

        # Excel Export (Ensures most recent benchmark data is included)
        try:
            bm_comp_df = None
            if args.benchmark and os.path.exists(screener.benchmark_path):
                bm_comp_df = pd.read_csv(screener.benchmark_path)
            screener.exporter.export(df, bm_comp_df)
        except Exception as e:
            logger.error(f"Failed to export Excel report: {str(e)}")
        
    except Exception as e:
        logger.critical(f"Critical error during execution: {str(e)}")
        import traceback
        logger.debug(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
