import pandas as pd
from typing import List, Dict, Any
import numpy as np
import os
import time
import ast
from .integrator import DataIntegrator
from ..models.magic_formula import MagicFormulaModel
from ..models.greenwald import GreenwaldModel
from ..models.dcf import DCFModel
from ..models.safety import SafetyModel
from ..models.equity_analysis import EquityAnalysisModel
from ..data.mf_provider import MagicFormulaProvider
from ..data.exceptions import ScreenerError
from ..data.schemas import FinancialStatement, MarketData
from ..utils.excel_exporter import ExcelExporter
import logging
import dataclasses

def is_financial_or_invalid(sic_code) -> bool:
    """Check if SIC code is None/empty, or in 6000-6999."""
    if sic_code is None or pd.isna(sic_code) or sic_code == "":
        return True
    try:
        sic_num = int(float(sic_code))
        return 6000 <= sic_num <= 6999
    except (ValueError, TypeError):
        return True

class Screener:
    """Orchestrates the screening process for multiple tickers."""
    
    def __init__(self, integrator: DataIntegrator, output_dir: str = "output"):
        self.integrator = integrator
        self.mf_model = MagicFormulaModel()
        self.gw_model = GreenwaldModel()
        self.dcf_model = DCFModel()
        self.safety_model = SafetyModel()
        self.equity_model = EquityAnalysisModel()
        self.exporter = ExcelExporter(output_dir)
        self.logger = logging.getLogger(__name__)
        self.output_dir = output_dir
        self.data_path = os.path.join(self.output_dir, "company_data.csv")
        self.benchmark_path = os.path.join(self.output_dir, "benchmark_comparison.csv")

    def run_equity_analysis(self, ticker: str, max_years: int = 20) -> Dict[str, float]:
        """Perform long-term equity recalculation and CAGR analysis."""
        try:
            hist_df = self.integrator.fetch_historical_data(ticker, max_years=max_years)
            if hist_df.empty:
                return {}
            return self.equity_model.calculate_metrics(hist_df)
        except Exception as e:
            self.logger.warning(f"Failed equity analysis for {ticker}: {e}")
            return {}

    def _calculate_industry_medians(self, companies_data):
        """Calculate median cash/revenue ratio per SIC code."""
        ratios = []
        for fs, md in companies_data:
            if fs and fs.revenue and fs.revenue > 0:
                ratio = (fs.cash_and_equivalents or 0) / fs.revenue
                ratios.append({
                    'sic_code': fs.sic_code,
                    'ratio': ratio
                })
        
        if not ratios:
            return {}, 0.1 # Default global median
            
        df_ratios = pd.DataFrame(ratios)
        global_median = df_ratios['ratio'].median()
        industry_medians = df_ratios.groupby('sic_code')['ratio'].agg(['median', 'count'])
        
        medians_dict = {}
        for sic, row in industry_medians.iterrows():
            if row['count'] < 3:
                medians_dict[sic] = global_median
            else:
                val = row['median']
                # if str(sic).startswith('283') and val > 0.5:
                #     val = 0.2 
                medians_dict[sic] = val
                
        return medians_dict, global_median

    def _save_raw_data(self, companies_data):
        """Save all fetched fundamental and market data to CSV, merging with existing cache."""
        new_rows = []
        for fs, md in companies_data:
            row = {**dataclasses.asdict(fs), **dataclasses.asdict(md)}
            new_rows.append(row)
        
        if not new_rows:
            return
            
        new_df = pd.DataFrame(new_rows)
        new_df = new_df.loc[:,~new_df.columns.duplicated()]
        
        if os.path.exists(self.data_path):
            try:
                existing_df = pd.read_csv(self.data_path)
                # Merge: update existing rows and append new ones
                # We use ticker as the key
                df = pd.concat([existing_df, new_df]).drop_duplicates(subset=['ticker'], keep='last')
            except Exception as e:
                self.logger.warning(f"Could not merge with existing cache: {e}")
                df = new_df
        else:
            df = new_df
            
        # Ensure we drop any financial or invalid companies from the merged dataset
        if 'sic_code' in df.columns:
            df = df[~df['sic_code'].apply(is_financial_or_invalid)]

        df.to_csv(self.data_path, index=False)
        self.logger.info(f"Aggregated data for {len(df)} companies saved to {self.data_path}")

    def _load_cached_data(self, tickers: List[str]):
        """Load data from aggregated CSV if available."""
        if not os.path.exists(self.data_path):
            return [], tickers
            
        try:
            df = pd.read_csv(self.data_path)
            # Filter for requested tickers
            df = df[df['ticker'].isin(tickers)]
            
            cached_data = []
            loaded_tickers = set()
            
            # Get fields from schemas
            fs_fields = FinancialStatement.__dataclass_fields__.keys()
            md_fields = MarketData.__dataclass_fields__.keys()
            
            for _, row in df.iterrows():
                # Reconstruct dataclasses
                fs_data = {k: row[k] for k in fs_fields if k in row and not pd.isna(row[k])}
                md_data = {k: row[k] for k in md_fields if k in row and not pd.isna(row[k])}
                
                # Handle types and nested objects
                if 'shares_outstanding' in fs_data: fs_data['shares_outstanding'] = int(fs_data['shares_outstanding'])
                if 'shares_outstanding' in md_data: md_data['shares_outstanding'] = int(md_data['shares_outstanding'])
                if 'sic_code' in fs_data: fs_data['sic_code'] = int(fs_data['sic_code'])
                
                # Parse revenue history from CSV string
                if 'revenue_history' in fs_data and isinstance(fs_data['revenue_history'], str):
                    try:
                        fs_data['revenue_history'] = ast.literal_eval(fs_data['revenue_history'])
                    except:
                        fs_data['revenue_history'] = {}
                
                fs = FinancialStatement(**fs_data)
                md = MarketData(**md_data)
                
                cached_data.append((fs, md))
                loaded_tickers.add(row['ticker'])
            
            remaining_tickers = [t for t in tickers if t not in loaded_tickers]
            self.logger.info(f"Loaded {len(cached_data)} companies from cache. {len(remaining_tickers)} to fetch.")
            
            return cached_data, remaining_tickers
        except Exception as e:
            self.logger.warning(f"Failed to load cache: {str(e)}. Proceeding with full fetch.")
            return [], tickers

    def run_benchmark_comparison(self, df_results: pd.DataFrame, thresholds: List[int] = list(range(100, 2000, 100)), force_refresh: bool = False):
        """Compare results with magicformulainvesting.com official data."""
        self.logger.info("Starting benchmark comparison with magicformulainvesting.com...")
        
        try:
            benchmark_raw_path = os.path.join(self.output_dir, "benchmark_mf.csv")
            
            if os.path.exists(benchmark_raw_path) and not force_refresh:
                self.logger.info(f"Loading benchmark data from {benchmark_raw_path}...")
                benchmark_df = pd.read_csv(benchmark_raw_path)
            else:
                mf_provider = MagicFormulaProvider()
                benchmark_df = mf_provider.run(thresholds=thresholds)
                
                if benchmark_df.empty:
                    self.logger.warning("No benchmark data retrieved.")
                    return
                
                # Save benchmark raw data for reference
                benchmark_df.to_csv(benchmark_raw_path, index=False)
            
            # Normalize tickers for matching
            df_results['Ticker'] = df_results['Ticker'].str.strip().str.upper()
            benchmark_df['Ticker'] = benchmark_df['Ticker'].str.strip().str.upper()

            # Enrichment logic (Phase 3)
            # 1. Prepare benchmark data: sort by threshold and drop duplicates to get first hit per ticker
            bm_mapping = benchmark_df.sort_values('threshold_marketCap').drop_duplicates(subset=['Ticker']).copy()
            bm_mapping = bm_mapping.rename(columns={
                'TopGreenblatt': 'MF_TopGreenblatt',
                'threshold_marketCap': 'MF_Threshold_marketCap_M'
            })[['Ticker', 'MF_TopGreenblatt', 'MF_Threshold_marketCap_M']]

            # 2. Merge with results
            enriched_df = df_results.merge(bm_mapping, on='Ticker', how='left')
            enriched_df['MF_TopGreenblatt'] = enriched_df['MF_TopGreenblatt'].fillna('Not Found')
            enriched_df['MF_Threshold_marketCap_M'] = enriched_df['MF_Threshold_marketCap_M'].fillna(0)

            # 3. Update the results file with enriched data
            enriched_df.to_csv(self.data_path, index=False)
            self.logger.info(f"Enriched results with benchmark data saved to {self.data_path}")

            # Update the reference for the rest of this method
            df_results = enriched_df

            comparison_results = []
            for cap in thresholds:
                # Filter benchmark for this threshold
                bm_top30 = benchmark_df[(benchmark_df['threshold_marketCap'] == cap) & (benchmark_df['TopGreenblatt'] == 'Top30')]['Ticker'].unique()
                bm_top50 = benchmark_df[(benchmark_df['threshold_marketCap'] == cap) & (benchmark_df['TopGreenblatt'] == 'Top50')]['Ticker'].unique()
                
                # Filter our results for this threshold (market cap in millions in provider, but in absolute in results)
                our_subset = df_results[df_results['market_cap'] >= cap * 1e6].copy()
                if len(our_subset) == 0:
                    continue
                
                # Recalculate ranks for this specific subset
                our_subset['EY Rank Sub'] = our_subset['EY (%)'].rank(ascending=False)
                our_subset['ROC Rank Sub'] = our_subset['ROC (%)'].rank(ascending=False)
                our_subset['Magic Rank Sub'] = our_subset['EY Rank Sub'] + our_subset['ROC Rank Sub']
                
                our_top30 = our_subset.sort_values("Magic Rank Sub").head(30)['Ticker'].unique()
                our_top50 = our_subset.sort_values("Magic Rank Sub").head(50)['Ticker'].unique()
                
                overlap30 = len(set(bm_top30).intersection(set(our_top30)))
                overlap50 = len(set(bm_top50).intersection(set(our_top50)))
                
                perc30 = (overlap30 / len(bm_top30) * 100) if len(bm_top30) > 0 else 0
                perc50 = (overlap50 / len(bm_top50) * 100) if len(bm_top50) > 0 else 0
                
                comparison_results.append({
                    "Threshold ($M)": cap,
                    "Our Count": len(our_subset),
                    "MF Top30 Count": len(bm_top30),
                    "MF Top50 Count": len(bm_top50),
                    "Overlap Top30 (%)": round(perc30, 2),
                    "Overlap Top50 (%)": round(perc50, 2)
                })
            
            df_comp = pd.DataFrame(comparison_results)
            df_comp.to_csv(self.benchmark_path, index=False)
            
            print("\n" + "="*80)
            print("MAGIC FORMULA OVERLAP COMPARISON")
            print("="*80)
            from tabulate import tabulate
            print(tabulate(df_comp, headers='keys', tablefmt='psql', showindex=False))
            print("="*80)
            print(f"Comparison results saved to {self.benchmark_path}")
            
            return df_results
            
        except Exception as e:
            self.logger.error(f"Error during benchmark comparison: {str(e)}")
            return df_results

    def screen_tickers(self, tickers: List[str], enrich: bool = False) -> pd.DataFrame:
        """Process a list of tickers and return a dataframe with all metrics."""
        from concurrent.futures import ThreadPoolExecutor
        from tqdm import tqdm
        
        discount_rate = self.integrator.get_discount_rate()
        
        # Load from cache first
        companies_data, tickers_to_fetch = self._load_cached_data(tickers)
        
        # Prune cached data: Remove financial and invalid companies
        companies_data = [d for d in companies_data if not is_financial_or_invalid(d[0].sic_code)]
        
        # Fetch remaining
        if tickers_to_fetch:
            self.logger.info(f"Fetching data for {len(tickers_to_fetch)} companies...")
            
            # Use a smaller worker pool and save periodically
            batch_size = 20
            new_data_total = []
            
            for i in range(0, len(tickers_to_fetch), batch_size):
                batch_tickers = tickers_to_fetch[i:i+batch_size]
                
                def fetch_data(ticker):
                    try:
                        fs, md = self.integrator.fetch_company_data(ticker, enrich=enrich)
                        if fs is None:
                            return None
                        return (fs, md)
                    except Exception as e:
                        self.logger.warning(f"Failed to fetch data for {ticker}: {str(e)}")
                        return None

                with ThreadPoolExecutor(max_workers=5) as executor:
                    batch_results = list(tqdm(executor.map(fetch_data, batch_tickers), 
                                             total=len(batch_tickers), 
                                             desc=f"Fetching batch {i//batch_size + 1}",
                                             leave=False))
                
                new_data = [d for d in batch_results if d is not None]
                if new_data:
                    # Prune newly fetched financial and invalid companies
                    new_data = [d for d in new_data if not is_financial_or_invalid(d[0].sic_code)]
                    
                    new_data_total.extend(new_data)
                    companies_data.extend(new_data)
                    # Incremental save of raw data
                    self._save_raw_data(companies_data)
        
        if not companies_data:
            return pd.DataFrame()

        # Pass 2: Industry medians
        industry_medians, global_median = self._calculate_industry_medians(companies_data)
        
        # Pass 3: Valuation models
        results = []
        for fs, md in tqdm(companies_data, desc="Calculating metrics"):
            try:
                industry_ratio = industry_medians.get(fs.sic_code, global_median)
                
                ey = self.mf_model.calculate_earnings_yield(fs, md, industry_ratio)
                roc = self.mf_model.calculate_roc(fs, md, industry_ratio)
                repro_val = self.gw_model.calculate_reproduction_value(fs)
                epv = self.gw_model.calculate_epv(fs, wacc=discount_rate)
                intrinsic_val = self.dcf_model.calculate_intrinsic_value(fs, discount_rate)
                
                # Safety Metrics (Phase 2)
                output_signal = self.safety_model.calculate_traffic_light(fs, md)
                
                # Ensure we handle the case where revenue_history might be None/Empty
                rev_history = fs.revenue_history if fs.revenue_history else {}
                rev_zscore_res = self.safety_model.calculate_revenue_zscore_label(rev_history)
                
                # Working Capital Anomaly Signal
                wc_anomaly_res = fs.wc_anomaly_signal if (hasattr(fs, 'wc_anomaly_signal') and fs.wc_anomaly_signal) else "N/A"
                ar_div_res = fs.ar_divergence if hasattr(fs, 'ar_divergence') else 0.0
                inv_div_res = fs.inv_divergence if hasattr(fs, 'inv_divergence') else 0.0
                if wc_anomaly_res == "N/A" and hasattr(fs, 'prev_revenue') and fs.prev_revenue and fs.prev_revenue > 0:
                    wc_calc = self.safety_model.calculate_working_capital_anomaly(
                        current_rev=fs.revenue,
                        prev_rev=fs.prev_revenue,
                        current_ar=fs.accounts_receivable,
                        prev_ar=fs.prev_accounts_receivable,
                        current_inv=fs.inventory,
                        prev_inv=fs.prev_inventory
                    )
                    wc_anomaly_res = wc_calc['wc_anomaly_signal']
                    ar_div_res = wc_calc['ar_divergence']
                    inv_div_res = wc_calc['inv_divergence']

                # Combine raw data and calculated metrics
                data = {**dataclasses.asdict(fs), **dataclasses.asdict(md)}
                data.update({
                    "Ticker": fs.ticker, # For display/match
                    "EY (%)": ey * 100,
                    "ROC (%)": roc * 100,
                    "tangible_capital_employed": self.mf_model.calculate_tangible_capital_employed(fs, industry_ratio),
                    "Repro Value": repro_val,
                    "EPV": epv,
                    "DCF Intrinsic": intrinsic_val,
                    "Industry Ratio": industry_ratio,
                    "Output": output_signal,
                    "Revenue ZScore": rev_zscore_res if rev_zscore_res else "N/A",
                    "WC Anomaly": wc_anomaly_res,
                    "AR Divergence (%)": ar_div_res,
                    "Inv Divergence (%)": inv_div_res
                })
                results.append(data)
            except Exception as e:
                self.logger.error(f"Error processing {fs.ticker}: {str(e)}")

        df = pd.DataFrame(results)
        if not df.empty:
            # Drop duplicate ticker column if any
            df = df.loc[:,~df.columns.duplicated()]
            
            # Global rankings
            df['EY Rank'] = df['EY (%)'].rank(ascending=False)
            df['ROC Rank'] = df['ROC (%)'].rank(ascending=False)
            df['Magic Rank'] = df['EY Rank'] + df['ROC Rank']
            # Sequential Rank (Item #13)
            df['Magic Formula Rank'] = df['Magic Rank'].rank(method='first').astype(int)
            
            df['EPV/MC'] = df['EPV'] / df['market_cap']
            df['DCF/MC'] = df['DCF Intrinsic'] / df['market_cap']
            
            # Additional Ratios (Phase 4)
            df['market_cap_musd'] = df['market_cap'] / 1e6
            
            # PE Ratio = Price / EPS
            # EPS = Net Income / Shares
            df['eps_ttm'] = df['net_income'] / df['shares_outstanding']
            df['pe_ratio'] = df['price'] / df['eps_ttm']
            
            # PB Ratio = Price / BVPS
            # Book Value Per Share = Equity / Shares
            df['bvps_ttm'] = df['shareholders_equity'] / df['shares_outstanding']
            df['pb_ratio'] = df['price'] / df['bvps_ttm']
            
            # Capital Structure E/D
            total_debt_series = df['short_term_debt'].fillna(0) + df['long_term_debt'].fillna(0)
            df['total_debt'] = total_debt_series
            df['e_over_d'] = df['shareholders_equity'] / total_debt_series
            
            # FCF Yield (%)
            if 'free_cash_flow' in df.columns:
                df['fcf_yield (%)'] = (df['free_cash_flow'] / df['market_cap'] * 100).replace([np.inf, -np.inf], np.nan).fillna(0)
            
            # Handle infinite/NaN ratios
            for col in ['pe_ratio', 'pb_ratio', 'e_over_d', 'fcf_yield (%)']:
                if col in df.columns:
                    df[col] = df[col].replace([np.inf, -np.inf], np.nan).fillna(0)
            
            # Save the full results (raw + metrics + ranks) to company_data.csv
            df.to_csv(self.data_path, index=False)
            self.logger.info(f"Full screening results with ranks saved to {self.data_path}")
            
        return df
