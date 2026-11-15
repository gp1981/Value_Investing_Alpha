# Business Requirements Document (BRD) - Value Investing Screener

## 1. Objective
Develop a Python-based screener that identifies undervalued companies by applying established value investing frameworks to SEC filing data and current market prices.

## 2. Target Frameworks

### 2.1 Magic Formula (Joel Greenblatt)
- **Earnings Yield**: EBIT / Enterprise Value.
- **Return on Capital (ROC)**: EBIT / (Net Working Capital + Net Fixed Assets).
- **Data Source**: SEC filings for EBIT, Assets, Liabilities; yfinance for Price/Market Cap.

### 2.2 Asset Reproduction Value & Earning Power Value (Bruce Greenwald)
- **Asset Reproduction Value**: Estimate the cost to reproduce the company's assets (Adjusted Balance Sheet).
- **Earning Power Value (EPV)**: Value of current earnings normalized and discounted at WACC.
- **Comparison**: Compare reproduction value, EPV, and Market Cap to identify moats and margins of safety.

### 2.3 Present Value of Free Cash Flow (DCF)
- **Applicability**: Steady-state businesses with low FCF volatility and high cash conversion.
- **Discount Rate**: 10-year historical S&P 500 return (dividends reinvested).
- **Methodology**: Multi-stage DCF or perpetuity model based on business maturity.

## 3. Functional Requirements

### 3.1 Data Acquisition
- **SEC Integration**: Automated retrieval of 10-K and 10-Q filings via `edgartools`.
- **Standardization**: Map various XBRL tags to a unified internal schema for fundamentals.
- **Market Data**: Fetch current price, shares outstanding, and market cap via `yfinance`.
- **Consistency Check**: Cross-verify shares outstanding between SEC and yfinance; default to SEC in case of conflict.

### 3.2 Screening & Ranking
- **Multi-Model Calculation**: Calculate all parameters (Magic Formula, Greenwald, DCF) for a given list of tickers.
- **Dynamic Ranking**: Allow the user to sort the results based on any of the core valuation criteria.
- **Parameter Visibility**: Display the intermediate fundamentals (EBIT, NWC, etc.) alongside the final scores.

### 3.4 Filtering
- **Industry Exclusions**: Automatically filter out companies in the financial sector (SIC codes 6000-6799) including Banks, Insurance, Investment Firms, and REITs to prevent data corruption.
- **Foreign/ADR Exclusions**: Identify and exclude foreign companies and ADRs using SEC filing history (e.g., Form 20-F, 40-F) to ensure data normalization and currency consistency.

## 4. Technical Constraints
- **Language**: Python 3.12+
- **Primary Data Source**: SEC (EDGAR) via `edgartools`.
- **Secondary Data Source**: Yahoo Finance via `yfinance`.
- **Architecture**: Modular, separation of concerns (Data, Logic, UI).
