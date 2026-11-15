import yfinance as yf
import pandas as pd
import os
from datetime import datetime
from .schemas import MarketData
from .exceptions import MarketDataError

class MarketDataProvider:
    """Retrieves market data (price, cap, shares) using yfinance."""
    
    CACHE_PATH = "tests/output/market_cap.csv"

    def get_market_caps(self, tickers: list[str], max_batches: int = None) -> dict[str, float]:
        """Fetch market caps for a list of tickers in optimized batches with local caching."""
        from tqdm import tqdm
        
        # Load cache if it exists
        if os.path.exists(self.CACHE_PATH):
            print(f"Loading cached market caps from {self.CACHE_PATH}")
            df = pd.read_csv(self.CACHE_PATH)
            cached_caps = dict(zip(df['Ticker'], df['Market_Cap']))
            # Filter tickers that are not in the cache to update them if necessary
            missing_tickers = [t for t in tickers if t not in cached_caps]
        else:
            cached_caps = {}
            missing_tickers = tickers

        caps = cached_caps
        if missing_tickers:
            batch_size = 200
            chunks = [missing_tickers[i:i + batch_size] for i in range(0, len(missing_tickers), batch_size)]
            
            if max_batches:
                chunks = chunks[:max_batches]
                
            for batch in tqdm(chunks, desc="Fetching missing market caps"):
                tickers_data = yf.Tickers(" ".join(batch))
                for ticker, ticker_obj in tickers_data.tickers.items():
                    info = ticker_obj.info
                    cap = info.get('marketCap', 0)
                    if cap:
                        caps[ticker] = float(cap)
            
            # Save updated cache
            os.makedirs(os.path.dirname(self.CACHE_PATH), exist_ok=True)
            pd.DataFrame(list(caps.items()), columns=['Ticker', 'Market_Cap']).to_csv(self.CACHE_PATH, index=False)
            
        return {t: caps[t] for t in tickers if t in caps}

    def get_market_data(self, ticker: str) -> MarketData:
        """Fetch real-time market data for a given ticker."""
        try:
            t = yf.Ticker(ticker)
            fast = t.fast_info
            
            # Use shares instead of shares_outstanding for fast_info
            shares = getattr(fast, 'shares', 0)
            if not shares:
                # Fallback to info (slower)
                shares = t.info.get('sharesOutstanding', 0)
                
            if not shares:
                 raise MarketDataError(f"Could not retrieve shares outstanding for {ticker}")

            return MarketData(
                ticker=ticker,
                price=float(fast.last_price),
                market_cap=float(fast.market_cap),
                shares_outstanding=int(shares),
                last_updated=datetime.now().isoformat()
            )
            
        except Exception as e:
            raise MarketDataError(f"Failed to fetch market data for {ticker}: {str(e)}")

    def get_sp500_annualized_return(self, years: int = 10) -> float:
        """Calculate the annualized return of the S&P 500 over a specified number of years."""
        try:
            def get_return(ticker, years):
                t = yf.Ticker(ticker)
                # Ensure we get Adj Close for accurate return calculations
                hist = t.history(period=f"{years}y", auto_adjust=False)
                
                if hist.empty or "Adj Close" not in hist.columns:
                    raise MarketDataError(f"Insufficient data for {ticker}")

                start_price = hist['Adj Close'].iloc[0]
                end_price = hist['Adj Close'].iloc[-1]
                
                total_return = (end_price / start_price) - 1
                annualized_return = (1 + total_return) ** (1/years) - 1
                return annualized_return

            gspc_return = get_return("^GSPC", years)
            sp500tr_return = get_return("^SP500TR", years)
            
            # Return the average as per requirement if they differ
            return (gspc_return + sp500tr_return) / 2
            
        except Exception as e:
            raise MarketDataError(f"Failed to calculate S&P 500 {years}-year annualized return: {str(e)}")
