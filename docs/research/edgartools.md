# edgartools Reference for Value Investing Screener

## Overview
edgartools is a Python library that provides structured access to SEC EDGAR filings, enabling the extraction of XBRL financial data into pandas DataFrames.

## Essential Configuration
Every script must identify itself to the SEC EDGAR system.
```python
from edgar import set_identity
set_identity("Your Name your.email@example.com")
```

## Core API Methods for Value Investing

### Company Lookup
```python
from edgar import Company
# Lookup by Ticker or CIK
company = Company("AAPL")
```

### Financial Statements
Retrieve standardized financial statements.
```python
financials = company.get_financials()

# Access Income Statement
income_df = financials.income_statement().to_dataframe()

# Access Balance Sheet
balance_sheet_df = financials.balance_sheet().to_dataframe()

# Access Cash Flow
cash_flow_df = financials.cash_flow().to_dataframe()
```

### Filing Access
Search and filter for specific forms (10-K, 10-Q, etc.).
```python
# Get all 10-K filings for a company
filings = company.get_filings(form="10-K")

# Get the latest filing
latest_10k = filings.latest
```

## Best Practices
- **Identity:** Always set identity at the entry point of your application.
- **DataFrames:** Use `.to_dataframe()` to convert extracted XBRL data into pandas DataFrames for easy numerical processing and integration with valuation models.
- **Error Handling:** Wrap SEC data retrieval in try-except blocks to handle network issues or missing filings for specific companies.
