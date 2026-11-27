try:
    from edgar.settings import set_identity
except ImportError:
    from edgar import set_identity
from edgar import Company, use_local_storage
from typing import Optional, List, Any, Dict
import pandas as pd
import re
from .schemas import FinancialStatement
from .exceptions import SECDataError
import logging
import os

class SECProvider:
    """Retrieves fundamental data from SEC filings with robust TTM derivation."""
    
    def __init__(self, identity: str = "Value Investing Screener screener@example.com", storage_dir: str = "output/"):
        set_identity(identity)
        self.logger = logging.getLogger(__name__)
        
        from src.utils.storage import resolve_edgar_paths
        data_path, cache_path, _ = resolve_edgar_paths(preferred_data_dir=storage_dir)
        
        self.storage_dir = os.path.dirname(data_path)
        self.data_path = data_path
        self.cache_path = cache_path
        
        # Set environment variables and use explicit config to avoid leakage
        os.environ['EDGAR_LOCAL_DATA_DIR'] = data_path
        os.environ['EDGAR_CACHE_DIR'] = cache_path
        
        # Use local storage ONLY if bulk data is actually populated; otherwise allow live SEC HTTP queries
        if self.is_storage_populated():
            use_local_storage(data_path)
        else:
            use_local_storage(False)

    def clear_cache(self):
        """
        Clears both memory and disk caches to prevent leakage and disk bloat.
        Targets the configured cache directory AND the default ~/.edgar location.
        """
        import shutil
        import sys
        
        self.logger.info("Clearing SEC caches...")

        # 1. Clear Memory Cache (LRU and EntityFacts caches in edgar library)
        try:
            from edgar import clear_company_facts_cache
            clear_company_facts_cache()
        except Exception as e:
            self.logger.debug(f"Could not clear company facts cache: {e}")

        try:
            from edgar import _tcache
            _tcache.clear()
        except ImportError:
            pass
        except Exception as e:
            self.logger.debug(f"Could not clear memory cache: {e}")

        # 2. Clear Configured Disk Cache
        cache_path = os.environ.get('EDGAR_CACHE_DIR')
        if cache_path and os.path.exists(cache_path):
            try:
                # Remove all files and subdirs in the cache path but keep the directory itself
                for filename in os.listdir(cache_path):
                    file_p = os.path.join(cache_path, filename)
                    if os.path.isfile(file_p) or os.path.islink(file_p):
                        os.unlink(file_p)
                    elif os.path.isdir(file_p):
                        shutil.rmtree(file_p)
                self.logger.debug(f"Cleared configured disk cache at: {cache_path}")
            except Exception as e:
                self.logger.warning(f"Failed to clear disk cache at {cache_path}: {e}")

        # 3. Clear Default OS Cache (~/.edgar) to prevent leaks
        home_edgar = os.path.expanduser("~/.edgar")
        if os.path.exists(home_edgar):
            try:
                # We only want to clear the 'cache' subdirectory if it exists to avoid deleting 'data'
                default_cache = os.path.join(home_edgar, "cache")
                if os.path.exists(default_cache):
                    shutil.rmtree(default_cache)
                    os.makedirs(default_cache, exist_ok=True)
                    self.logger.debug(f"Cleared default leaked cache at: {default_cache}")
                
                # Also check for any loose files in ~/.edgar that might be cache
                for item in os.listdir(home_edgar):
                    item_path = os.path.join(home_edgar, item)
                    # Don't touch 'data' or 'submissions' if the user happens to have them there
                    if item not in ['data', 'submissions'] and os.path.isfile(item_path):
                        os.unlink(item_path)
            except Exception as e:
                self.logger.debug(f"Could not clear ~/.edgar: {e}")

    def is_storage_populated(self) -> bool:
        """Check if the local storage directory contains filing data."""
        if not os.path.exists(self.data_path):
            return False
        # Check submissions subdirectory first
        # Check standard edgartools bulk directories; ignore _tcache / .migrations
        for subdir in ("submissions", "companyfacts"):
            target_dir = os.path.join(self.data_path, subdir)
            if os.path.exists(target_dir):
                try:
                    if len(os.listdir(target_dir)) > 0:
                        return True
                except Exception:
                    pass
        return False

    def sync_storage(self):
        """Bulk download EDGAR data to the configured local storage directory."""
        from edgar import download_edgar_data
        
        data_dir = os.path.join(self.storage_dir, "data")
        cache_dir = os.path.join(self.storage_dir, "cache")
        
        self.logger.info(f"Syncing data to: {data_dir}")
        self.logger.info(f"Temporary cache set to: {cache_dir}")

        try:
            download_edgar_data()
            self.logger.info("Success! Data and cache are now fully external.")
        except PermissionError as e:
            self.logger.error(f"Permission Error: {e}. Try running 'sudo chmod -R 755 ~/.edgar' in Terminal.")
            raise SECDataError(f"Permission error during sync: {e}")
        except Exception as e:
            self.logger.error(f"An unexpected error occurred: {e}")
            raise SECDataError(f"Unexpected error during sync: {e}")

    def _get_period_columns(self, df: pd.DataFrame) -> Dict[str, Optional[str]]:
        """Identify current YTD, previous YTD, and FY columns."""
        if df is None or df.empty:
            return {}
            
        internal_cols = {'concept', 'label', 'standard_concept', 'level', 'abstract', 'dimension', 
                         'is_breakdown', 'dimension_axis', 'dimension_member', 'dimension_member_label', 
                         'dimension_label', 'balance', 'weight', 'preferred_sign', 'parent_concept', 
                         'parent_abstract_concept'}
        
        cols = [c for c in df.columns if c not in internal_cols]
        
        res = {"curr_ytd": None, "prev_ytd": None, "fy": None}
        
        # Priority: (YTD) > (FY) > Date strings
        ytd_cols = sorted([c for c in cols if "(YTD)" in str(c)], reverse=True)
        if len(ytd_cols) >= 1: res["curr_ytd"] = ytd_cols[0]
        if len(ytd_cols) >= 2: res["prev_ytd"] = ytd_cols[1]
        
        fy_cols = sorted([c for c in cols if "FY" in str(c)], reverse=True)
        if fy_cols: res["fy"] = fy_cols[0]
        
        # Fallback: find most recent date-like columns
        if not res["curr_ytd"]:
            date_cols = sorted([c for c in cols if re.search(r'\d{4}-\d{2}-\d{2}', str(c))], reverse=True)
            if date_cols: res["curr_ytd"] = date_cols[0]
            if len(date_cols) >= 2: res["prev_ytd"] = date_cols[1]
            
        return res

    def _get_standard_value(self, df: pd.DataFrame, column: str, std_concept: str) -> float:
        """Helper to extract value by standard concept. If multiple rows found, returns the first."""
        if df is None or df.empty or not column or 'standard_concept' not in df.columns:
            return 0.0
        
        row = df[df['standard_concept'] == std_concept]
        if not row.empty:
            val = row[column].iloc[0]
            return float(val) if pd.notnull(val) else 0.0
        return 0.0

    def _get_total_standard_value(self, df: pd.DataFrame, column: str, std_concept: str) -> float:
        """Helper to extract and SUM values for a standard concept, avoiding double counting of parents/subtotals."""
        if df is None or df.empty or not column or 'standard_concept' not in df.columns:
            return 0.0
        
        # 1. Filter rows by standard concept
        rows = df[df['standard_concept'] == std_concept]
        if rows.empty:
            return 0.0
            
        # 2. To avoid double counting subtotals, only include rows whose parent is NOT also mapped to the SAME standard concept.
        # This effectively picks the most granular (leaf) components if they are all mapped to the same concept,
        # OR it picks the total if only the total is mapped to that concept.
        concepts_in_set = set(rows['concept'].dropna())
        
        # If 'parent_concept' column exists, use the hierarchy logic
        if 'parent_concept' in rows.columns:
            # We want rows that are NOT parents of other rows in the same set, OR
            # simpler: rows whose parent is NOT in the set.
            # If a row's parent is also in the set, then this row is a component and the parent is a subtotal.
            # We want to keep the subtotals if possible, or the components.
            
            # Actually, the logic should be: if a parent is in the set, the parent is a subtotal.
            # If we want the most granular items, we keep rows that are NOT parents of any other row in the set.
            # If we want the most aggregated items, we keep rows whose parent is NOT in the set.
            
            # Let's re-test KO Cash:
            # R2 (comp), R3 (comp), R4 (total), R5 (other)
            # R2 parent is R4. R3 parent is R4. R4 parent is Assets (not in set). R5 parent is Assets (not in set).
            # If we take rows whose parent is NOT in set, we get R4 and R5. Correct!
            
            leaf_rows = rows[~rows['parent_concept'].isin(concepts_in_set)]
            
            if not leaf_rows.empty:
                return float(leaf_rows[column].sum())
            
        # Fallback if parent_concept missing or logic above yielded nothing
        # Filter out rows that are explicitly marked as breakdowns to avoid double counting
        if 'is_breakdown' in rows.columns:
            non_breakdowns = rows[rows['is_breakdown'] == False]
            if not non_breakdowns.empty:
                return float(non_breakdowns[column].sum())
            
        return float(rows[column].sum())

    def _derive_ebit_period(self, df: pd.DataFrame, col: str) -> float:
        """Derive EBIT for a single period using multiple fallbacks."""
        if not col: return 0.0
        
        # 1. Standard Concept: Operating Income (Gold standard)
        ebit = self._get_standard_value(df, col, "OperatingIncomeLoss")
        if ebit != 0: return ebit
        
        # 2. Pretax fallback (Best proxy for holding companies/conglomerates)
        pretax = self._get_standard_value(df, col, "PretaxIncomeLoss")
        if pretax != 0: return pretax
        
        # 3. CostsSubtotal fallback
        revenue = self._get_standard_value(df, col, "Revenue")
        costs_subtotal = self._get_standard_value(df, col, "CostsSubtotal")
        if revenue > 0 and costs_subtotal > 0:
            return revenue - costs_subtotal
            
        # 4. Component fallback
        cogs = self._get_standard_value(df, col, "CostOfGoodsAndServicesSold")
        sga = self._get_standard_value(df, col, "SellingGeneralAndAdminExpenses")
        rd = self._get_standard_value(df, col, "ResearchAndDevelopmentExpenses")
        if revenue > 0:
            return revenue - (cogs or 0) - (sga or 0) - (rd or 0)
            
        return 0.0

    def get_historical_data(self, ticker: str, max_years: int = 20) -> pd.DataFrame:
        """Fetch up to N years of historical data for equity analysis, including latest 10-Q/K."""
        try:
            company = Company(ticker)
            data = []
            seen_dates = set()

            # 1. Process latest filing (K or Q) as the most recent snapshot
            all_filings = company.get_filings(form=["10-K", "10-Q"], amendments=False)
            latest_filing = all_filings.latest() if all_filings else None
            if latest_filing:
                processed = self._process_single_filing(latest_filing)
                if processed:
                    data.append(processed)
                    seen_dates.add(processed['date'])

            # 2. Try fast historical series from company.facts (pre-cached local storage facts)
            facts_loaded = False
            if hasattr(company, 'facts') and company.facts:
                try:
                    facts = company.facts
                    bs = facts.balance_sheet(annual=True, as_dataframe=True, periods=max_years)
                    inc = facts.income_statement(annual=True, as_dataframe=True, periods=max_years)
                    cf = facts.cash_flow_statement(annual=True, as_dataframe=True, periods=max_years)

                    if bs is not None and not bs.empty and inc is not None and not inc.empty and cf is not None and not cf.empty:
                        meta_cols = {'label', 'depth', 'is_abstract', 'is_total', 'section', 'confidence'}
                        fy_cols = [c for c in bs.columns if c not in meta_cols and 'FY' in str(c)]

                        def _get_val(df_stmt, concepts, column):
                            for conc in concepts:
                                if conc in df_stmt.index:
                                    v = df_stmt.loc[conc, column]
                                    if pd.notnull(v):
                                        return float(v)
                            return 0.0

                        for col in sorted(fy_cols):
                            yr_match = re.search(r'\d{4}', str(col))
                            if not yr_match:
                                continue
                            yr = int(yr_match.group(0))
                            dt = pd.to_datetime(f"{yr}-12-31")

                            if dt in seen_dates:
                                continue

                            eq = _get_val(bs, ['StockholdersEquity', 'AllEquityBalanceIncludingMinorityInterest',
                                               'StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest',
                                               'CommonStockholdersEquity', 'CommonEquity'], col)
                            ni = _get_val(inc, ['NetIncomeLoss', 'ProfitLoss', 'NetIncome'], col)
                            divs = _get_val(cf, ['PaymentsOfDividendsCommonStock', 'PaymentsOfDividends', 'DistributionsToMinorityInterests'], col)
                            repurchases = _get_val(cf, ['PaymentsForRepurchaseOfCommonStock', 'EquityExpenseIncome(BuybackIssued)'], col)
                            issuances = _get_val(cf, ['ProceedsFromIssuanceOfCommonStock'], col)

                            std = _get_val(bs, ['ShortTermDebt', 'LongTermDebtCurrent'], col)
                            ltd = _get_val(bs, ['LongTermDebt', 'LongTermDebtNoncurrent'], col)

                            data.append({
                                "date": dt,
                                "equity": eq,
                                "net_income": ni,
                                "dividends": -abs(divs),
                                "repurchases": -abs(repurchases),
                                "issuances": issuances,
                                "total_debt": std + ltd
                            })
                            seen_dates.add(dt)

                        if len(data) >= 2:
                            facts_loaded = True
                except Exception as e:
                    self.logger.debug(f"Fast historical facts extraction failed for {ticker}: {e}")

            # 3. Fallback: Process historical 10-Ks if facts extraction did not yield sufficient history
            if not facts_loaded:
                filings_10k = company.get_filings(form="10-K", amendments=False)
                if filings_10k:
                    for filing in filings_10k[:max_years]:
                        if pd.to_datetime(filing.filing_date) in seen_dates:
                            continue
                        processed = self._process_single_filing(filing)
                        if processed:
                            data.append(processed)
                            seen_dates.add(processed['date'])

            return pd.DataFrame(data).sort_values("date") if data else pd.DataFrame()

        except Exception as e:
            self.logger.error(f"Error fetching historical SEC data for {ticker}: {str(e)}")
            return pd.DataFrame()

    def _process_single_filing(self, filing) -> Optional[Dict[str, Any]]:
        """Extracts key items from a single XBRL filing."""
        try:
            xbrl = filing.xbrl()
            if not xbrl: return None
            
            bs = xbrl.statements.balance_sheet()
            is_stmt = xbrl.statements.income_statement()
            cf = xbrl.statements.cash_flow_statement()
            
            if not bs or not is_stmt or not cf: return None
            
            df_bs = bs.to_dataframe()
            df_is = is_stmt.to_dataframe()
            df_cf = cf.to_dataframe()
            
            cols_bs = self._get_period_columns(df_bs)
            cols_is = self._get_period_columns(df_is)
            cols_cf = self._get_period_columns(df_cf)
            
            col_bs = cols_bs.get("fy") or cols_bs.get("curr_ytd")
            col_is = cols_is.get("fy") or cols_is.get("curr_ytd")
            col_cf = cols_cf.get("fy") or cols_cf.get("curr_ytd")
            
            # Unified Equity mapping (matches get_financials)
            equity = self._get_total_standard_value(df_bs, col_bs, "AllEquityBalanceIncludingMinorityInterest")
            if equity == 0:
                equity = self._get_total_standard_value(df_bs, col_bs, "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest")
            if equity == 0:
                equity = self._get_total_standard_value(df_bs, col_bs, "StockholdersEquity")
            if equity == 0:
                equity = self._get_total_standard_value(df_bs, col_bs, "AllEquityBalance")
            if equity == 0:
                equity = self._get_total_standard_value(df_bs, col_bs, "CommonEquity")
                
            net_income = self._get_total_standard_value(df_is, col_is, "NetIncome")
            
            # CF Items
            divs = self._get_total_standard_value(df_cf, col_cf, "PaymentsOfDividendsCommonStock")
            if divs == 0:
                divs = self._get_total_standard_value(df_cf, col_cf, "PaymentsOfDividends")
            if divs == 0:
                divs = self._get_total_standard_value(df_cf, col_cf, "DistributionsToMinorityInterests")
                
            repurchases = self._get_total_standard_value(df_cf, col_cf, "PaymentsForRepurchaseOfCommonStock")
            if repurchases == 0:
                repurchases = self._get_total_standard_value(df_cf, col_cf, "EquityExpenseIncome(BuybackIssued)")
                
            issuances = self._get_total_standard_value(df_cf, col_cf, "ProceedsFromIssuanceOfCommonStock")
            
            # Debt
            std = self._get_total_standard_value(df_bs, col_bs, "ShortTermDebt")
            if std == 0:
                std = self._get_total_standard_value(df_bs, col_bs, "LongTermDebtCurrent")
            ltd = self._get_total_standard_value(df_bs, col_bs, "LongTermDebt")
            if ltd == 0:
                ltd = self._get_total_standard_value(df_bs, col_bs, "LongTermDebtNoncurrent")
                
            return {
                "date": pd.to_datetime(filing.filing_date),
                "equity": equity,
                "net_income": net_income,
                "dividends": divs,
                "repurchases": repurchases,
                "issuances": issuances,
                "total_debt": std + ltd
            }
        except Exception as e:
            self.logger.debug(f"Error processing filing {filing.filing_date}: {e}")
            return None

    def get_working_capital_metrics(self, ticker: str, company: Optional[Any] = None) -> Dict[str, float]:
        """
        Fast extraction of current and previous year Revenue, Accounts Receivable, and Inventory from company.facts.
        Returns dict with current and previous period values.
        """
        try:
            if company is None:
                company = Company(ticker)
            if hasattr(company, 'facts') and company.facts:
                inc = company.facts.income_statement(periods=2, period='annual', as_dataframe=True)
                bs = company.facts.balance_sheet(periods=2, period='annual', as_dataframe=True)
                
                meta_cols = {'label', 'depth', 'is_abstract', 'is_total', 'section', 'confidence'}
                inc_cols = [c for c in inc.columns if c not in meta_cols] if inc is not None and not inc.empty else []
                bs_cols = [c for c in bs.columns if c not in meta_cols] if bs is not None and not bs.empty else []

                # Extract Revenue
                c_rev, p_rev = 0.0, 0.0
                if inc is not None and not inc.empty and len(inc_cols) >= 1:
                    rev_row = None
                    for conc in ['RevenueFromContractWithCustomerExcludingAssessedTax', 'SalesRevenueNet', 'Revenues', 'Revenue']:
                        if conc in inc.index:
                            rev_row = inc.loc[conc]
                            break
                    if rev_row is None:
                        for idx, row in inc.iterrows():
                            lbl = str(row.get('label', '')).lower()
                            if 'revenue' in lbl or 'sales' in lbl:
                                rev_row = row
                                break
                    if rev_row is not None:
                        c_rev = float(rev_row[inc_cols[0]]) if pd.notnull(rev_row[inc_cols[0]]) else 0.0
                        if len(inc_cols) >= 2 and pd.notnull(rev_row[inc_cols[1]]):
                            p_rev = float(rev_row[inc_cols[1]])

                # Extract Accounts Receivable
                c_ar, p_ar = 0.0, 0.0
                if bs is not None and not bs.empty and len(bs_cols) >= 1:
                    ar_row = None
                    for conc in ['AccountsReceivableNetCurrent', 'AccountsReceivableCurrent', 'ReceivablesNetCurrent', 'TradeReceivables']:
                        if conc in bs.index:
                            ar_row = bs.loc[conc]
                            break
                    if ar_row is None:
                        for idx, row in bs.iterrows():
                            lbl = str(row.get('label', '')).lower()
                            if 'receivable' in lbl and 'current' in lbl:
                                ar_row = row
                                break
                    if ar_row is not None:
                        c_ar = float(ar_row[bs_cols[0]]) if pd.notnull(ar_row[bs_cols[0]]) else 0.0
                        if len(bs_cols) >= 2 and pd.notnull(ar_row[bs_cols[1]]):
                            p_ar = float(ar_row[bs_cols[1]])

                # Extract Inventory
                c_inv, p_inv = 0.0, 0.0
                if bs is not None and not bs.empty and len(bs_cols) >= 1:
                    inv_row = None
                    for conc in ['Inventories', 'InventoryNet', 'InventoryGross']:
                        if conc in bs.index:
                            inv_row = bs.loc[conc]
                            break
                    if inv_row is None:
                        for idx, row in bs.iterrows():
                            lbl = str(row.get('label', '')).lower()
                            if 'inventor' in lbl:
                                inv_row = row
                                break
                    if inv_row is not None:
                        c_inv = float(inv_row[bs_cols[0]]) if pd.notnull(inv_row[bs_cols[0]]) else 0.0
                        if len(bs_cols) >= 2 and pd.notnull(inv_row[bs_cols[1]]):
                            p_inv = float(inv_row[bs_cols[1]])

                return {
                    'current_rev': c_rev,
                    'prev_rev': p_rev,
                    'current_ar': c_ar,
                    'prev_ar': p_ar,
                    'current_inv': c_inv,
                    'prev_inv': p_inv
                }
        except Exception as e:
            self.logger.debug(f"Fast WC extraction failed for {ticker}: {e}")

        return {
            'current_rev': 0.0, 'prev_rev': 0.0,
            'current_ar': 0.0, 'prev_ar': 0.0,
            'current_inv': 0.0, 'prev_inv': 0.0
        }

    def get_financials(self, ticker: str, exclude_adr: bool = False, enrich: bool = False) -> Any:
        try:
            company = Company(ticker)
            if exclude_adr and company.is_foreign:
                return None
            
            cik_padded = str(company.cik).zfill(10)
            local_sub = os.path.join(self.data_path, "submissions", f"CIK{cik_padded}.json")
            local_facts = os.path.join(self.data_path, "companyfacts", f"CIK{cik_padded}.json")
            
            # Check if company data is locally present in submissions or companyfacts
            is_local = os.path.exists(local_sub) or os.path.exists(local_facts)
            if not is_local and not enrich:
                self.logger.warning(f"Skipping {ticker}: No local data found and enrichment disabled.")
                return None

            if is_local:
                print(f"[DATA SOURCE] {ticker}: Retrieved from LOCAL STORAGE")
            else:
                print(f"[DATA SOURCE] {ticker}: Retrieved from SEC (Enrichment Mode)")

            filings = company.get_filings(form=["10-K", "10-Q"])
            if not filings:
                self.logger.warning(f"No 10-K or 10-Q filings found for {ticker}")
                return None

            latest = filings.latest()
            if not latest:
                return None

            xbrl_latest = latest.xbrl()
            if not xbrl_latest or not hasattr(xbrl_latest, "statements") or not xbrl_latest.statements:
                self.logger.warning(f"No XBRL statements available in latest filing for {ticker}")
                return None
            
            # Balance Sheet (Snapshot)
            bs_df = xbrl_latest.statements.balance_sheet().to_dataframe()
            bs_cols = self._get_period_columns(bs_df)
            bs_col = bs_cols.get("curr_ytd") or bs_cols.get("fy")
            
            total_assets = self._get_total_standard_value(bs_df, bs_col, "Assets")
            if total_assets == 0:
                total_assets = self._get_total_standard_value(bs_df, bs_col, "LiabilitiesAndEquity")

            # Robust Equity mapping
            # 1. Total Equity (including minority interest) - Best for balancing L = A - E
            equity = self._get_total_standard_value(bs_df, bs_col, "AllEquityBalanceIncludingMinorityInterest")
            if equity == 0:
                equity = self._get_total_standard_value(bs_df, bs_col, "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest")
            
            # 2. Shareholders' Equity (excluding minority interest)
            if equity == 0:
                equity = self._get_total_standard_value(bs_df, bs_col, "StockholdersEquity")
            if equity == 0:
                equity = self._get_total_standard_value(bs_df, bs_col, "AllEquityBalance")
            if equity == 0:
                equity = self._get_total_standard_value(bs_df, bs_col, "CommonEquity")
            
            # Robust Liabilities mapping
            total_liabilities = self._get_total_standard_value(bs_df, bs_col, "Liabilities")
            
            # Fallback for Liabilities: Assets - Equity (Highly reliable if both A and E are found)
            if total_liabilities == 0 and total_assets != 0 and equity != 0:
                derived_liab = total_assets - equity
                if derived_liab > 0:
                    total_liabilities = derived_liab

            if total_liabilities == 0:
                # Try summing current and non-current
                liab_curr = self._get_total_standard_value(bs_df, bs_col, "CurrentLiabilitiesTotal")
                liab_noncurr = self._get_total_standard_value(bs_df, bs_col, "NonCurrentLiabilitiesTotal")
                if liab_curr != 0 or liab_noncurr != 0:
                    total_liabilities = liab_curr + liab_noncurr
            
            current_assets = self._get_total_standard_value(bs_df, bs_col, "CurrentAssetsTotal")
            if current_assets == 0:
                current_assets = self._get_total_standard_value(bs_df, bs_col, "CurrentAssets")
                
            current_liabilities = self._get_total_standard_value(bs_df, bs_col, "CurrentLiabilitiesTotal")
            if current_liabilities == 0:
                current_liabilities = self._get_total_standard_value(bs_df, bs_col, "CurrentLiabilities")
                
            cash = self._get_total_standard_value(bs_df, bs_col, "CashAndMarketableSecurities")
            if cash == 0:
                cash = self._get_total_standard_value(bs_df, bs_col, "Cash")
            if cash == 0:
                cash = self._get_total_standard_value(bs_df, bs_col, "CashAndCashEquivalentsAtCarryingValue")

            nfa = self._get_total_standard_value(bs_df, bs_col, "PlantPropertyEquipmentNet")
            ar = self._get_total_standard_value(bs_df, bs_col, "TradeReceivables")
            if ar == 0:
                ar = self._get_total_standard_value(bs_df, bs_col, "AccountsReceivableCurrent")

            inventory = self._get_total_standard_value(bs_df, bs_col, "Inventories")
            if inventory == 0:
                inventory = self._get_total_standard_value(bs_df, bs_col, "InventoryNet")

            std = self._get_total_standard_value(bs_df, bs_col, "ShortTermDebt")
            ltd = self._get_total_standard_value(bs_df, bs_col, "LongTermDebt")
            
            # Robust Goodwill and Intangibles mapping
            gw = self._get_total_standard_value(bs_df, bs_col, "Goodwill")
            
            # Sum all potential intangible asset tags
            ia_total = 0.0
            for ia_concept in ["IntangibleAssets", "IntangibleAssetsNetExcludingGoodwill", 
                               "FiniteLivedIntangibleAssetsNet", "IndefiniteLivedIntangibleAssetsExcludingGoodwill"]:
                ia_total += self._get_total_standard_value(bs_df, bs_col, ia_concept)
                
            goodwill = gw + ia_total
            
            # Robust Payables mapping
            ap = self._get_total_standard_value(bs_df, bs_col, "AccountsPayableCurrent")
            if ap == 0:
                ap = self._get_total_standard_value(bs_df, bs_col, "TradePayables")

            # TTM Income/CashFlow logic
            if latest.form == '10-K':
                is_df = xbrl_latest.statements.income_statement().to_dataframe()
                cf_df = xbrl_latest.statements.cash_flow_statement().to_dataframe()
                is_col = self._get_period_columns(is_df).get("fy")
                cf_col = self._get_period_columns(cf_df).get("fy")
                
                ebit = self._derive_ebit_period(is_df, is_col)
                revenue = self._get_total_standard_value(is_df, is_col, "Revenue")
                net_income = self._get_total_standard_value(is_df, is_col, "NetIncome")
                da = self._get_total_standard_value(cf_df, cf_col, "DepreciationExpense")
                capex = self._get_total_standard_value(cf_df, cf_col, "CapitalExpenses")
                interest = self._get_total_standard_value(is_df, is_col, "InterestExpense")
                tax = self._get_total_standard_value(is_df, is_col, "IncomeTaxes")
                ocf = self._get_total_standard_value(cf_df, cf_col, "NetCashProvidedByUsedInOperatingActivities")
                if ocf == 0:
                    ocf = self._get_total_standard_value(cf_df, cf_col, "OperatingCashFlow")
                fcf = ocf - capex if ocf != 0 else 0.0
            else:
                is_q_df = xbrl_latest.statements.income_statement().to_dataframe()
                cf_q_df = xbrl_latest.statements.cash_flow_statement().to_dataframe()
                q_cols = self._get_period_columns(is_q_df)
                
                prev_10k = filings.filter(form="10-K").latest()
                xbrl_k = prev_10k.xbrl()
                is_k_df = xbrl_k.statements.income_statement().to_dataframe()
                cf_k_df = xbrl_k.statements.cash_flow_statement().to_dataframe()
                k_cols = self._get_period_columns(is_k_df)
                
                def derive_ttm(df_q, col_q, df_k, col_k, concept, is_ebit=False):
                    if is_ebit:
                        curr_ytd = self._derive_ebit_period(df_q, col_q.get("curr_ytd"))
                        prev_ytd = self._derive_ebit_period(df_q, col_q.get("prev_ytd"))
                        prev_fy = self._derive_ebit_period(df_k, col_k.get("fy"))
                    else:
                        curr_ytd = self._get_total_standard_value(df_q, col_q.get("curr_ytd"), concept)
                        prev_ytd = self._get_total_standard_value(df_q, col_q.get("prev_ytd"), concept)
                        prev_fy = self._get_total_standard_value(df_k, col_k.get("fy"), concept)
                    return curr_ytd + prev_fy - prev_ytd

                ebit = derive_ttm(is_q_df, q_cols, is_k_df, k_cols, None, is_ebit=True)
                revenue = derive_ttm(is_q_df, q_cols, is_k_df, k_cols, "Revenue")
                net_income = derive_ttm(is_q_df, q_cols, is_k_df, k_cols, "NetIncome")
                da = derive_ttm(cf_q_df, q_cols, cf_k_df, k_cols, "DepreciationExpense")
                capex = derive_ttm(cf_q_df, q_cols, cf_k_df, k_cols, "CapitalExpenses")
                interest = derive_ttm(is_q_df, q_cols, is_k_df, k_cols, "InterestExpense")
                tax = derive_ttm(is_q_df, q_cols, is_k_df, k_cols, "IncomeTaxes")
                ocf = derive_ttm(cf_q_df, q_cols, cf_k_df, k_cols, "NetCashProvidedByUsedInOperatingActivities")
                if ocf == 0:
                    ocf = derive_ttm(cf_q_df, q_cols, cf_k_df, k_cols, "OperatingCashFlow")
                fcf = ocf - capex if ocf != 0 else 0.0

            # Fallback for OCF / FCF via edgartools standardized financials getter if zero
            if ocf == 0 or fcf == 0:
                try:
                    fin = company.get_financials()
                    if fin:
                        if ocf == 0:
                            f_ocf = fin.get_operating_cash_flow()
                            if f_ocf: ocf = float(f_ocf)
                        if fcf == 0:
                            f_fcf = fin.get_free_cash_flow()
                            if f_fcf: fcf = float(f_fcf)
                except Exception:
                    pass

            # Enrichment Logic (Phase 2 & 3 - Descriptions and History)
            rev_history = {}
            description = "N/A"
            
            if enrich:
                # Revenue History (Last 8 periods for Z-Score)
                # First try fast extraction from company.facts (pre-cached local storage)
                try:
                    if hasattr(company, 'facts') and company.facts:
                        inc_q = company.facts.income_statement(periods=8, period='quarterly', as_dataframe=True)
                        if inc_q is not None and not inc_q.empty:
                            meta_cols = {'label', 'depth', 'is_abstract', 'is_total', 'section', 'confidence'}
                            q_cols = [c for c in inc_q.columns if c not in meta_cols]
                            rev_row = None
                            for conc in ['RevenueFromContractWithCustomerExcludingAssessedTax', 'SalesRevenueNet', 'Revenues', 'Revenue']:
                                if conc in inc_q.index:
                                    rev_row = inc_q.loc[conc]
                                    break
                            if rev_row is None:
                                for idx, row in inc_q.iterrows():
                                    lbl = str(row.get('label', '')).lower()
                                    if 'revenue' in lbl or 'sales' in lbl:
                                        rev_row = row
                                        break
                            if rev_row is not None:
                                for q_col in q_cols:
                                    val = rev_row[q_col]
                                    if pd.notnull(val) and float(val) > 0:
                                        m = re.match(r'(Q\d)\s*(\d{4})', str(q_col))
                                        key = f"{m.group(2)}-{m.group(1)}" if m else str(q_col)
                                        rev_history[key] = float(val)
                except Exception as e:
                    self.logger.debug(f"Fast revenue extraction failed for {ticker}: {e}")

                # Fallback: if facts extraction yielded fewer than 2 periods, use filing loop
                if len(rev_history) < 2:
                    hist_filings = filings.filter(form=["10-K", "10-Q"])[:8]
                    for f in hist_filings:
                        try:
                            f_xbrl = f.xbrl()
                            f_is = f_xbrl.statements.income_statement().to_dataframe()
                            cols = self._get_period_columns(f_is)
                            col = cols.get("curr_ytd") or cols.get("fy")
                            rev = self._get_standard_value(f_is, col, "Revenue")
                            rev_history[str(f.filing_date)] = rev
                        except:
                            continue

                # Company Description (Item 1 from latest 10-K)
                try:
                    latest_10k_filing = filings.filter(form="10-K").latest()
                    if latest_10k_filing:
                        tenk = latest_10k_filing.obj()
                        item_1 = tenk.get('Item 1')
                        if item_1:
                            clean_desc = re.sub('<[^<]+?>', '', str(item_1))
                            description = clean_desc[:2000].strip()
                except Exception as e:
                    self.logger.warning(f"Could not extract description for {ticker}: {str(e)}")

                # Working Capital Anomaly Data
                wc_data = {'current_rev': 0.0, 'prev_rev': 0.0, 'current_ar': 0.0, 'prev_ar': 0.0, 'current_inv': 0.0, 'prev_inv': 0.0}
                wc_anomaly_signal = "N/A"
                ar_div = 0.0
                inv_div = 0.0
                try:
                    wc_data = self.get_working_capital_metrics(ticker, company)
                    from ..models.safety import SafetyModel
                    safety_m = SafetyModel()
                    cur_r = wc_data['current_rev'] if wc_data.get('current_rev', 0) > 0 else (revenue or 0.0)
                    cur_a = wc_data['current_ar'] if wc_data.get('current_ar', 0) > 0 else (ar or 0.0)
                    cur_i = wc_data['current_inv'] if wc_data.get('current_inv', 0) > 0 else (inventory or 0.0)
                    wc_res = safety_m.calculate_working_capital_anomaly(
                        current_rev=cur_r,
                        prev_rev=wc_data['prev_rev'],
                        current_ar=cur_a,
                        prev_ar=wc_data['prev_ar'],
                        current_inv=cur_i,
                        prev_inv=wc_data['prev_inv']
                    )
                    wc_anomaly_signal = wc_res['wc_anomaly_signal']
                    ar_div = wc_res['ar_divergence']
                    inv_div = wc_res['inv_divergence']
                except Exception as e:
                    self.logger.debug(f"Could not compute WC anomaly for {ticker}: {e}")

            # Robust Shares mapping
            shares = company.shares_outstanding
            if not shares or shares == 0:
                is_df = xbrl_latest.statements.income_statement().to_dataframe()
                is_cols = self._get_period_columns(is_df)
                is_col = is_cols.get("curr_ytd") or is_cols.get("fy")
                
                shares = self._get_standard_value(is_df, is_col, "WeightedAverageNumberOfDilutedSharesOutstanding")
                if shares == 0:
                    shares = self._get_standard_value(is_df, is_col, "SharesFullyDilutedAverage")
                if shares == 0:
                    shares = self._get_standard_value(is_df, is_col, "WeightedAverageNumberOfSharesOutstandingBasic")
                if shares == 0:
                    shares = self._get_standard_value(is_df, is_col, "SharesAverage")

            return FinancialStatement(
                ticker=ticker,
                ebit=ebit,
                total_assets=total_assets,
                total_liabilities=total_liabilities,
                current_assets=current_assets,
                current_liabilities=current_liabilities,
                cash_and_equivalents=cash,
                short_term_debt=std,
                long_term_debt=ltd,
                net_fixed_assets=nfa,
                shares_outstanding=int(shares) if shares else 0,
                company_name=company.name,
                description=description,
                sic_code=company.sic,
                industry=company.industry,
                accounts_receivable=ar,
                inventory=inventory,
                revenue=revenue,
                operating_income=ebit,
                net_income=net_income,
                depreciation_amortization=da,
                capex=capex,
                goodwill_and_intangible_assets=goodwill,
                shareholders_equity=equity,
                accounts_payable=ap,
                interest_expense_ttm=interest,
                income_tax_expense_ttm=tax,
                operating_cash_flow=ocf,
                free_cash_flow=fcf,
                revenue_history=rev_history,
                prev_revenue=wc_data.get('prev_rev', 0.0) if enrich else 0.0,
                prev_accounts_receivable=wc_data.get('prev_ar', 0.0) if enrich else 0.0,
                prev_inventory=wc_data.get('prev_inv', 0.0) if enrich else 0.0,
                wc_anomaly_signal=wc_anomaly_signal if enrich else "N/A",
                ar_divergence=ar_div if enrich else 0.0,
                inv_divergence=inv_div if enrich else 0.0
            )
            
        except Exception as e:
            self.logger.error(f"Error fetching SEC data for {ticker}: {str(e)}")
            raise SECDataError(f"Failed to fetch SEC data for {ticker}: {str(e)}")

    def get_filings(
        self,
        ticker: str,
        forms: Optional[List[str]] = None,
        limit: int = 50,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve recent official SEC filings (10-K, 10-Q, 8-K, 13F-HR, DEF 14A, 4, etc.)
        with optional form and date-range filtering.
        """
        if forms is None:
            forms = ["10-K", "10-Q", "8-K", "DEF 14A", "13F-HR", "4"]
        try:
            company = Company(ticker)
            kwargs: Dict[str, Any] = {}
            if forms:
                kwargs["form"] = forms
            if start_date or end_date:
                kwargs["filing_date"] = f"{start_date or ''}:{end_date or ''}"
            filings = company.get_filings(**kwargs)
            if not filings:
                return []

            items = []
            for f in filings[:limit]:
                f_date = str(f.filing_date) if f.filing_date else ""
                if start_date and f_date and f_date < start_date:
                    continue
                if end_date and f_date and f_date > end_date:
                    continue

                acc_num = getattr(f, "accession_number", getattr(f, "accession_no", ""))
                acc_nodash = acc_num.replace("-", "")
                primary_doc = getattr(f, "primary_document", "")
                cik = getattr(company, "cik", "")

                interactive_url = None
                if primary_doc and cik and acc_nodash:
                    interactive_url = f"https://www.sec.gov/ix?doc=/Archives/edgar/data/{cik}/{acc_nodash}/{primary_doc}"

                filing_url = getattr(f, "url", getattr(f, "homepage_url", ""))
                if not filing_url and acc_num and cik:
                    filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_nodash}/{acc_num}-index.html"

                items.append({
                    "form": str(f.form),
                    "filing_date": f_date,
                    "report_date": str(getattr(f, "report_date", "")) if getattr(f, "report_date", None) else None,
                    "accession_number": acc_num,
                    "description": str(getattr(f, "primary_doc_description", "") or f.form),
                    "url": filing_url,
                    "interactive_url": interactive_url
                })
                if len(items) >= limit:
                    break
            return items
        except Exception as e:
            self.logger.warning(f"Could not fetch filings for {ticker}: {e}")
            return []
