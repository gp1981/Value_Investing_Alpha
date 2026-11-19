import pandas as pd
import os
from datetime import datetime
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.styles import Alignment, Font

class ExcelExporter:
    """Handles formatted Excel export for screener results and benchmarks."""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        self.column_map = {
            "Output": "Output",
            "Revenue ZScore": "Outlier Revenue ZScore",
            "WC Anomaly": "WC Anomaly Signal",
            "AR Divergence (%)": "AR Divergence (%)",
            "Inv Divergence (%)": "Inv Divergence (%)",
            "MF_TopGreenblatt": "MF_TopGreenblatt",
            "MF_Threshold_marketCap_M": "MF_Threshold_marketCap_M",
            "Ticker": "Ticker",
            "company_name": "Company Name",
            "description": "Company Description",
            "industry": "Industry",
            "market_cap_musd": "Market Cap MUSD",
            "Magic Formula Rank": "Magic Formula Rank",
            "EY (%)": "Earnings Yield (%)",
            "ROC (%)": "Return On Capital (%)",
            "pe_ratio": "PriceToEarningsRatioTTM",
            "pb_ratio": "PriceToNetBookValueTTM",
            "fcf_yield (%)": "FCF Yield (%)",
            "e_over_d": "Capital_Structure E_over_D",
            "free_cash_flow": "free_cash_flow_ttm",
            "operating_cash_flow": "operating_cash_flow_ttm",
            "ebit": "ebit_ttm",
            "total_debt": "total_debt",
            "cash_and_equivalents": "cash_and_equivalents",
            "tangible_capital_employed": "tangible_capital_employed",
            "total_assets": "total_assets",
            "goodwill_and_intangible_assets": "goodwill_and_intangible_assets",
            "total_liabilities": "total_liabilities",
            "revenue": "revenue_ttm",
            "operating_income": "operating_income_ttm",
            "net_income": "net_income_ttm",
            "capex": "capex_ttm",
            "depreciation_amortization": "da_ttm",
            "interest_expense_ttm": "interest_expense_ttm",
            "income_tax_expense_ttm": "income_tax_expense_ttm",
            "CAGR Full Equity (%)": "CAGR Full Equity (%)",
            "CAGR Full Equity NI (%)": "CAGR Full Equity NI (%)",
            "Years Analyzed": "Historical Years Analyzed",
            "Initial Equity": "Initial Equity (Historical)",
            "Last Equity": "Last Equity (Current)",
            "Total cum. Dividends Paid": "Total cum. Dividends Paid",
            "Total cum. Net Repurchases": "Total cum. Net Repurchases",
            "Total cum. Debt Change": "Total cum. Debt Change",
            "Total cum. Net Income": "Total cum. Net Income"
        }

    def export(self, df_results: pd.DataFrame, df_benchmark: pd.DataFrame = None, custom_filename: str = None):
        """
        Creates a multi-sheet Excel file with formatted tables.
        
        Args:
            df_results: Main screener results
            df_benchmark: Optional benchmark performance summary
            custom_filename: Optional specific path to save the report
        """
        if custom_filename:
            filepath = custom_filename
        else:
            date_str = datetime.now().strftime("%Y%m%d")
            filename = f"company_data_{date_str}.xlsx"
            filepath = os.path.join(self.output_dir, filename)

        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # 1. Screener Results Sheet
            self._write_screener_sheet(df_results, writer)
            
            # 2. Benchmark Performance Sheet (if available)
            if df_benchmark is not None and not df_benchmark.empty:
                df_benchmark.to_excel(writer, sheet_name='Benchmark Performance', index=False)
                self._format_as_table(writer.book['Benchmark Performance'], "BenchmarkTable")

        print(f"Excel report generated: {filepath}")
        return filepath

    def _write_screener_sheet(self, df: pd.DataFrame, writer: pd.ExcelWriter):
        """Prepares and writes the main screener results sheet."""
        # Filter to requested columns only and rename
        existing_cols = [c for c in self.column_map.keys() if c in df.columns]
        export_df = df[existing_cols].rename(columns=self.column_map)

        # Write to Excel
        export_df.to_excel(writer, sheet_name='Screener Results', index=False)
        
        # Apply Table Formatting
        self._format_as_table(writer.book['Screener Results'], "ScreenerTable")

    def _format_as_table(self, ws, table_name: str):
        """Converts an existing worksheet range into an Excel Table with styles."""
        if ws.max_row <= 1:
            return

        # Define table range
        from openpyxl.utils import get_column_letter
        last_col = get_column_letter(ws.max_column)
        table_range = f"A1:{last_col}{ws.max_row}"
        
        tab = Table(displayName=table_name, ref=table_range)

        # Add a default style with striped rows and banded columns
        style = TableStyleInfo(name="TableStyleMedium9", showFirstColumn=False,
                               showLastColumn=False, showRowStripes=True, showColumnStripes=False)
        tab.tableStyleInfo = style
        ws.add_table(tab)
        
        # Basic layout adjustments
        for cell in ws[1]: # Header row
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')
        
        # Auto-adjust column widths (approximate)
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50) # Cap width
            ws.column_dimensions[column].width = adjusted_width
