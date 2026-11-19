import os
import sys
import argparse
import logging
import pandas as pd
from tqdm import tqdm
import ast

# Ensure the root directory is in the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

def enrich_data():
    parser = argparse.ArgumentParser(description="Enrich screener results with descriptions and historical data.")
    parser.add_argument("--tickers", nargs="+", help="Specific tickers to enrich. If omitted, enriches the top ranked ones.")
    parser.add_argument("--limit", type=int, default=50, help="Number of top-ranked tickers to enrich if no specific tickers provided.")
    parser.add_argument("--identity", default="Value Investing Screener screener@example.com", help="SEC User-Agent identity")
    parser.add_argument("--storage", default="/Volumes/T3/edgartools", help="edgartools local storage directory")
    parser.add_argument("--file", help="Path to a CSV or XLSX file containing tickers to enrich.")
    parser.add_argument("--description", action="store_true", help="Fetch latest company description.")
    parser.add_argument("--zscore", action="store_true", help="Fetch 8-quarter revenue history for Z-Score calculation.")
    parser.add_argument("--cagr", action="store_true", help="Fetch 20-year historical data for Full Equity CAGR analysis.")
    parser.add_argument("--metrics", nargs="+", help="Specific metrics to enrich (e.g., 'CAGR Full Equity (%%)' 'Initial Equity').")
    parser.add_argument("--incremental", action="store_true", help="Skip tickers that already have a description in the file.")
    
    args = parser.parse_args()

    # Determine what to fetch based on flags
    fetch_description = args.description
    fetch_zscore = args.zscore
    fetch_cagr = args.cagr
    specific_metrics = args.metrics if args.metrics else []
    
    # If no specific group flags provided, check metrics or default to all
    if not any([fetch_description, fetch_zscore, fetch_cagr]) and not specific_metrics:
        fetch_description = True
        fetch_zscore = True
        fetch_cagr = True

    # Mapping of metrics to their required fetch groups
    cagr_group = {
        "CAGR Full Equity (%)", "CAGR Full Equity NI (%)",
        "Years Analyzed", "Initial Equity", "Last Equity", "Total cum. Dividends Paid",
        "Total cum. Net Repurchases", "Total cum. Debt Change", "Total cum. Net Income"
    }
    zscore_group = {"Revenue ZScore", "revenue_history"}
    desc_group = {"description", "company_name", "industry", "sic_code"}
    fundamental_group = {"shareholders_equity", "accounts_payable", "interest_expense_ttm", "income_tax_expense_ttm"}
    wc_group = {"WC Anomaly", "wc_anomaly_signal", "AR Divergence (%)", "ar_divergence", "Inv Divergence (%)", "inv_divergence"}

    # Automatically enable groups if specific metrics from them are requested
    if any(m in cagr_group for m in specific_metrics): fetch_cagr = True
    if any(m in zscore_group for m in specific_metrics): fetch_zscore = True
    if any(m in desc_group for m in specific_metrics): fetch_description = True
    if any(m in wc_group for m in specific_metrics): fetch_description = True

    # CRITICAL: Set environment variables BEFORE any edgartools imports.
    os.environ['EDGAR_LOCAL_DATA_DIR'] = os.path.join(args.storage, "data")
    os.environ['EDGAR_CACHE_DIR'] = os.path.join(args.storage, "cache")

    from src.data.sec_provider import SECProvider
    from src.data.market_provider import MarketDataProvider
    from src.engine.integrator import DataIntegrator
    from src.engine.screener import Screener
    
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logger = logging.getLogger("Enrichment")

    # Load target tickers and dataframe
    target_file_df = None
    if args.file:
        if not os.path.exists(args.file):
            logger.error(f"Error: File {args.file} not found.")
            return
        
        logger.info(f"Loading tickers from file: {args.file}")
        if args.file.endswith('.csv'):
            target_file_df = pd.read_csv(args.file)
        elif args.file.endswith('.xlsx'):
            target_file_df = pd.read_excel(args.file)
        else:
            logger.error("Error: Unsupported file format. Use .csv or .xlsx")
            return
            
        # Find ticker column
        ticker_col = None
        for col in ['Ticker', 'ticker', 'TICKER']:
            if col in target_file_df.columns:
                ticker_col = col
                break
        
        if not ticker_col:
            logger.error(f"Error: Could not find a 'Ticker' column in {args.file}")
            return
            
        if args.incremental and 'description' in target_file_df.columns:
            missing_mask = target_file_df['description'].isna() | (target_file_df['description'] == 'N/A') | (target_file_df['description'] == '')
            df_to_process = target_file_df[missing_mask]
            logger.info(f"Incremental mode: Found {len(df_to_process)} tickers missing description out of {len(target_file_df)} total.")
            tickers_to_enrich = df_to_process[ticker_col].dropna().unique().tolist()
        else:
            tickers_to_enrich = target_file_df[ticker_col].dropna().unique().tolist()
            
        tickers_to_enrich = [str(t).upper() for t in tickers_to_enrich]
    else:
        data_path = "output/company_data.csv"
        if not os.path.exists(data_path):
            logger.error(f"Error: {data_path} not found. Run the main screener first.")
            return

        df = pd.read_csv(data_path)
        if df.empty:
            logger.error("Error: company_data.csv is empty.")
            return

        if args.tickers:
            tickers_to_enrich = [t.upper() for t in args.tickers]
        else:
            if 'Magic Rank' in df.columns:
                top_df = df.sort_values("Magic Rank").head(args.limit)
                tickers_to_enrich = top_df['ticker'].tolist()
            else:
                tickers_to_enrich = df['ticker'].head(args.limit).tolist()

    if not tickers_to_enrich:
        logger.info("No tickers identified for enrichment.")
        return

    logger.info(f"Starting enrichment for {len(tickers_to_enrich)} tickers...")
    if fetch_description: logger.info("  - Target: Latest Company Description")
    if fetch_zscore: logger.info("  - Target: 8-Quarter Revenue history (Z-Score)")
    if fetch_cagr: logger.info("  - Target: 20-Year Full Equity history (CAGR)")

    sec = SECProvider(identity=args.identity, storage_dir=args.storage)
    market = MarketDataProvider()
    integrator = DataIntegrator(sec, market)
    screener = Screener(integrator)

    # Column aliases to map renamed columns in Excel back to raw names or check values
    column_aliases = {
        'company_name': ['Company Name', 'company_name', 'COMPANY_NAME'],
        'industry': ['Industry', 'industry', 'INDUSTRY'],
        'description': ['Company Description', 'description', 'Company Description (Enriched)'],
        'sic_code': ['SIC', 'sic_code', 'sic'],
        'interest_expense_ttm': ['interest_expense_ttm', 'interest_expense', 'Interest Expense'],
        'income_tax_expense_ttm': ['income_tax_expense_ttm', 'income_tax_expense', 'Income Tax Expense'],
        'shareholders_equity': ['shareholders_equity', 'Shareholders Equity', 'Shareholders\' Equity'],
        'Output': ['Output', 'output'],
        'Revenue ZScore': ['Outlier Revenue ZScore', 'Revenue ZScore'],
        'accounts_payable': ['accounts_payable', 'Accounts Payable'],
        'CAGR Full Equity (%)': ['CAGR Full Equity (%)', 'CAGR Full Equity %'],
        'CAGR Full Equity NI (%)': ['CAGR Full Equity NI (%)', 'CAGR Full Equity NI %'],
        'Years Analyzed': ['Historical Years Analyzed', 'Years Analyzed'],
        'Initial Equity': ['Initial Equity (Historical)', 'Initial Equity'],
        'Last Equity': ['Last Equity (Current)', 'Last Equity'],
        'Total cum. Dividends Paid': ['Total cum. Dividends Paid', 'Total Dividends Paid (Cum)', 'Total Dividends Paid'],
        'Total cum. Net Repurchases': ['Total cum. Net Repurchases', 'Total Net Repurchases (Cum)', 'Total Net Repurchases'],
        'Total cum. Debt Change': ['Total cum. Debt Change', 'Total Debt Change (Cum)', 'Total Debt Change'],
        'Total cum. Net Income': ['Total cum. Net Income', 'Total Net Income (Cum)', 'Total Net Income'],
        'WC Anomaly': ['WC Anomaly Signal', 'WC Anomaly', 'wc_anomaly_signal'],
        'wc_anomaly_signal': ['WC Anomaly Signal', 'WC Anomaly', 'wc_anomaly_signal'],
        'AR Divergence (%)': ['AR Divergence (%)', 'AR Divergence %', 'ar_divergence'],
        'ar_divergence': ['AR Divergence (%)', 'AR Divergence %', 'ar_divergence'],
        'Inv Divergence (%)': ['Inv Divergence (%)', 'Inv Divergence %', 'inv_divergence'],
        'inv_divergence': ['Inv Divergence (%)', 'Inv Divergence %', 'inv_divergence']
    }

    def check_filled(df, ticker, ticker_col, raw_key):
        aliases = column_aliases.get(raw_key, [raw_key])
        col = next((c for c in aliases if c in df.columns), None)
        if not col:
            return False
        row_idx = df[df[ticker_col] == ticker].index
        if row_idx.empty:
            return False
        val = df.loc[row_idx[0], col]
        return pd.notnull(val) and val != "N/A" and val != ""

    enrich_map = {}
    batch_size = 25
    total_tickers = len(tickers_to_enrich)
    
    for i in range(0, total_tickers, batch_size):
        batch = tickers_to_enrich[i : i + batch_size]
        batch_num = (i // batch_size) + 1
        logger.info(f"\nProcessing Batch {batch_num} ({len(batch)} tickers)...")
        
        for ticker in tqdm(batch, desc=f"Batch {batch_num}"):
            try:
                full_data_row = {}
                
                # Determine what we actually need for this ticker if it's from a file
                # Skip fields that are already populated if we are in incremental mode or just to be efficient
                local_fetch_desc = fetch_description
                local_fetch_zscore = fetch_zscore
                local_fetch_cagr = fetch_cagr
                
                if target_file_df is not None:
                    # Skip description if already there
                    if fetch_description and check_filled(target_file_df, ticker, ticker_col, 'description'):
                        local_fetch_desc = False
                        
                    # Skip CAGR if CAGR is already there
                    if fetch_cagr and check_filled(target_file_df, ticker, ticker_col, 'CAGR Full Equity (%)'):
                        local_fetch_cagr = False
                            
                # 1. Fetch Z-Score and Description data if requested
                if local_fetch_desc or local_fetch_zscore:
                    fs, md = integrator.fetch_company_data(ticker, enrich=True)
                    if fs and md:
                        output_signal = screener.safety_model.calculate_traffic_light(fs, md)
                        rev_zscore = screener.safety_model.calculate_revenue_zscore_label(fs.revenue_history or {})
                        
                        from dataclasses import asdict
                        fs_dict = asdict(fs)
                        
                        full_data_row.update({
                            'description': fs_dict.get('description', 'N/A'),
                            'revenue_history': str(fs_dict.get('revenue_history', {})),
                            'company_name': fs_dict.get('company_name', 'N/A'),
                            'industry': fs_dict.get('industry', 'N/A'),
                            'sic_code': fs_dict.get('sic_code', 'N/A'),
                            'Output': output_signal,
                            'Revenue ZScore': rev_zscore,
                            'shareholders_equity': fs_dict.get('shareholders_equity', 0.0),
                            'accounts_payable': fs_dict.get('accounts_payable', 0.0),
                            'interest_expense_ttm': fs_dict.get('interest_expense_ttm', 0.0),
                            'income_tax_expense_ttm': fs_dict.get('income_tax_expense_ttm', 0.0),
                            'WC Anomaly': fs_dict.get('wc_anomaly_signal', 'N/A'),
                            'wc_anomaly_signal': fs_dict.get('wc_anomaly_signal', 'N/A'),
                            'AR Divergence (%)': fs_dict.get('ar_divergence', 0.0),
                            'ar_divergence': fs_dict.get('ar_divergence', 0.0),
                            'Inv Divergence (%)': fs_dict.get('inv_divergence', 0.0),
                            'inv_divergence': fs_dict.get('inv_divergence', 0.0)
                        })
                
                # 2. Fetch Equity Analysis if requested
                if local_fetch_cagr:
                    equity_res = screener.run_equity_analysis(ticker, max_years=20)
                    full_data_row.update(equity_res)
                
                # 3. Filter for specific metrics if requested
                if specific_metrics:
                    data_row = {k: v for k, v in full_data_row.items() if k in specific_metrics}
                else:
                    data_row = full_data_row
                    
                if data_row:
                    enrich_map[ticker] = data_row
                    
            except Exception as e:
                logger.warning(f"Failed to enrich {ticker}: {e}")

        # BATCH SAVE
        if enrich_map:
            logger.info(f"Batch {batch_num} complete. Saving progress...")
            
            if target_file_df is not None:
                # Map columns in enrich_df to existing columns in target_file_df or standard aliases to prevent duplicates
                mapped_enrich_map = {}
                for tick, row in enrich_map.items():
                    mapped_row = {}
                    for k, v in row.items():
                        # Find if there is an existing alias in target_file_df
                        aliases = column_aliases.get(k, [k])
                        found_col = next((c for c in aliases if c in target_file_df.columns), None)
                        if found_col:
                            mapped_row[found_col] = v
                        else:
                            # Use first alias for Excel, or raw key for CSV
                            if args.file.endswith('.xlsx'):
                                mapped_row[aliases[0]] = v
                            else:
                                mapped_row[k] = v
                    mapped_enrich_map[tick] = mapped_row

                enrich_df = pd.DataFrame.from_dict(mapped_enrich_map, orient='index').reset_index().rename(columns={'index': ticker_col})
                
                # CRITICAL (Issue #22): DataFrame.update() routes through pandas'
                # internal block manager which refuses to upcast a consolidated
                # float64 block to object, even after explicit astype() calls.
                # We bypass this entirely by merging column-by-column using
                # combine_first semantics: prefer non-NaN values from enrich_df,
                # keep existing values for tickers not in enrich_df.
                enrich_indexed = enrich_df.set_index(ticker_col)
                target_indexed = target_file_df.set_index(ticker_col)

                for col in enrich_indexed.columns:
                    enrich_col = enrich_indexed[col]
                    if col not in target_indexed.columns:
                        # New column: add it directly
                        target_indexed[col] = enrich_col
                    else:
                        # Existing column: overwrite only where enrich has a non-NaN value.
                        # Cast both sides to object first to avoid block-manager upcast errors.
                        target_col = target_indexed[col].astype(object)
                        enrich_col = enrich_col.astype(object)
                        # Align on index, then fill only non-NaN positions from enrich
                        target_col.update(enrich_col)
                        target_indexed[col] = target_col

                target_file_df = target_indexed.reset_index()

                
                if args.file.endswith('.csv'):
                    target_file_df.to_csv(args.file, index=False)
                else:
                    # Restore table format by using ExcelExporter
                    try:
                        # Load any existing Benchmark Performance sheet
                        bm_df = None
                        if os.path.exists(args.file):
                            try:
                                bm_df = pd.read_excel(args.file, sheet_name='Benchmark Performance')
                            except Exception:
                                pass
                        
                        # Map all current column names back to their raw versions so ExcelExporter maps them properly
                        export_df = target_file_df.copy()
                        rev_column_map = {v: k for k, v in screener.exporter.column_map.items()}
                        export_df = export_df.rename(columns=rev_column_map)
                        
                        screener.exporter.export(export_df, df_benchmark=bm_df, custom_filename=args.file)
                    except Exception as e:
                        logger.error(f"Failed to apply table formatting to {args.file}: {e}")
                        target_file_df.to_excel(args.file, index=False)

            data_path = "output/company_data.csv"
            if os.path.exists(data_path):
                master_df = pd.read_csv(data_path)
                
                # CRITICAL: Ensure object type for update to prevent LossySetitemError (Issue #19)
                for col in ['description', 'revenue_history', 'Output', 'Revenue ZScore', 'company_name', 'sic_code', 'ticker']:
                    if col in master_df.columns:
                        master_df[col] = master_df[col].astype(object)
                
                update_df = pd.DataFrame.from_dict(enrich_map, orient='index').reset_index().rename(columns={'index': 'ticker'})
                
                # Ensure update_df also uses object type for these columns
                for col in ['sic_code', 'ticker']:
                    if col in update_df.columns:
                        update_df[col] = update_df[col].astype(object)

                master_df = master_df.set_index('ticker')
                update_df = update_df.set_index('ticker')
                for col in update_df.columns:
                    enrich_col = update_df[col]
                    if col not in master_df.columns:
                        master_df[col] = enrich_col
                    else:
                        target_col = master_df[col].astype(object)
                        enrich_col = enrich_col.astype(object)
                        target_col.update(enrich_col)
                        master_df[col] = target_col
                master_df = master_df.reset_index()
                master_df.to_csv(data_path, index=False)

                # File-based enrichment already exported the requested target file above.
                # Avoid exporting the broader master cache over that file, especially when
                # the target uses the same date-based filename as the default report.
                if not args.file:
                    try:
                        bm_comp_df = None
                        if os.path.exists(screener.benchmark_path):
                            bm_comp_df = pd.read_csv(screener.benchmark_path)
                        export_df = master_df.copy()
                        if 'Magic Rank' in export_df.columns:
                            export_df = export_df.sort_values("Magic Rank")
                        screener.exporter.export(export_df, bm_comp_df)
                    except Exception as e:
                        logger.error(f"Failed to update main Excel report: {e}")

        sec.clear_cache()
        enrich_map = {}
        
    logger.info("\nEnrichment complete.")
    if args.file: logger.info(f"Final file saved to: {args.file}")

if __name__ == "__main__":
    enrich_data()
