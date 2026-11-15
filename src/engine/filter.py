import pandas as pd
import edgar
from tqdm import tqdm
from edgar.reference import CompanySubset
from src.data.market_provider import MarketDataProvider
from src.data.sec_provider import SECProvider
import os

try:
    from edgar.settings import set_identity
except ImportError:
    from edgar import set_identity

# Set identity for edgartools
set_identity("Value Investing Screener screener@example.com")

class CompanyFilter:
    def __init__(self, market_data: MarketDataProvider, sec_provider: SECProvider):
        self.market_data = market_data
        self.sec_provider = sec_provider

    def get_candidate_companies(self, exchange_list=["NYSE", "Nasdaq", "NYSEAMER","OTC","CBOE"]):
        """Retrieves bulk company list."""
        print("Retrieving company subset from SEC reference...")
        subsets = []
        for exchange in tqdm(exchange_list, desc="Retrieving exchanges"):
            try:
                subset = CompanySubset().from_exchange(exchange).get()
                subsets.append(subset)
            except Exception as e:
                print(f"Warning: Failed to retrieve data for {exchange}: {str(e)}")
        
        if not subsets:
            return pd.DataFrame()
            
        return pd.concat(subsets)

    def apply_industry_filters(self, df: pd.DataFrame):
        """Stage 1: Exclude companies by SIC codes. 
        Enriches data from cache if available to improve early filtering.
        """
        print("Applying SIC exclusions...")
        
        # Check for SIC column
        sic_col = 'sic' if 'sic' in df.columns else 'sic_code'
        
        # Enrichment: If column is missing or has many NaNs, try to pull from company_data.csv
        cache_path = "output/company_data.csv"
        if os.path.exists(cache_path) and (sic_col not in df.columns or df[sic_col].isna().sum() > len(df)/2):
            try:
                cache_df = pd.read_csv(cache_path)
                sic_col_cache = 'sic' if 'sic' in cache_df.columns else 'sic_code'
                if 'ticker' in cache_df.columns and sic_col_cache in cache_df.columns:
                    ticker_to_sic = cache_df.dropna(subset=[sic_col_cache]).set_index('ticker')[sic_col_cache].to_dict()
                    if sic_col not in df.columns:
                        df[sic_col] = df['ticker'].map(ticker_to_sic)
                    else:
                        df[sic_col] = df[sic_col].fillna(df['ticker'].map(ticker_to_sic))
            except Exception as e:
                # Silently fail enrichment
                pass

        if sic_col in df.columns:
            df[sic_col] = pd.to_numeric(df[sic_col], errors='coerce')
            
            # Identify tickers that are already cached
            cached_tickers = set()
            cache_path = "output/company_data.csv"
            if os.path.exists(cache_path):
                try:
                    cache_df = pd.read_csv(cache_path)
                    if 'ticker' in cache_df.columns:
                        cached_tickers = set(cache_df['ticker'].dropna().unique())
                except Exception:
                    pass

            def should_exclude(row):
                val = row[sic_col]
                ticker = row.get('ticker')
                if pd.notnull(val):
                    return 6000 <= val <= 6999
                else:
                    # If SIC is NaN/None, exclude ONLY if it is in the cache (meaning we fetched it and it lacked an SIC)
                    return ticker in cached_tickers

            df = df[~df.apply(should_exclude, axis=1)]
            
        return df.copy()

    def apply_foreign_filter(self, df: pd.DataFrame):
        """Stage 1.5: Exclude foreign/ADR companies using fast metadata with fallback."""
        print("Applying ADR/foreign exclusions...")
        valid_tickers = []
        
        for _, row in tqdm(df.iterrows(), total=len(df), desc="Checking ADRs"):
            try:
                company = edgar.Company(row['ticker'])
                # Fast check using company.is_foreign metadata
                if hasattr(company, 'is_foreign') and company.is_foreign is not None:
                    if not company.is_foreign:
                        valid_tickers.append(row['ticker'])
                    continue
                
                # Fallback to checking foreign filing types
                filings = company.get_filings(form=["20-F", "40-F", "F-1"])
                if len(filings) == 0:
                    valid_tickers.append(row['ticker'])
            except Exception:
                # Keep if lookup fails to avoid data loss
                valid_tickers.append(row['ticker'])
        return df[df['ticker'].isin(valid_tickers)].copy()

    def apply_market_cap_filters(self, df: pd.DataFrame, min_market_cap: float = 50e6, max_batches: int = None):
        """Stage 2 & 3: Fetch market caps and apply threshold."""
        tickers = df['ticker'].dropna().tolist()
        print(f"Fetching market caps for {len(tickers)} companies...")
        
        market_caps = self.market_data.get_market_caps(tickers, max_batches=max_batches)
        df['market_cap'] = df['ticker'].map(market_caps)
        
        # Filter by market cap
        df = df.dropna(subset=['market_cap'])
        return df[df['market_cap'] > min_market_cap]

    def run(self, output_path: str = "data/filtered_companies.csv"):
        df = self.get_candidate_companies()
        
        # Stage 1: Industry (Fastest - Local data only)
        df = self.apply_industry_filters(df)
        
        # Stage 1.5: ADR (Medium - Network request per company)
        df = self.apply_foreign_filter(df)
        
        # Stage 2: Market Cap (Slowest - Expensive API request per company)
        filtered_df = self.apply_market_cap_filters(df)
        
        filtered_df.to_csv(output_path, index=False)
        print(f"Filtered list saved to {output_path}")
        return filtered_df
