# Stage 2 Extensibility Roadmap — Advanced SEC edgartools Features

> **Architecture & Implementation Plan for Post-MVP Features**  
> Direct integration with [dgunning/edgartools](https://github.com/dgunning/edgartools) capabilities for deep institutional ownership, insider trading, material event monitoring, and governance analysis.

---

## 1. Overview of Stage 2 Vision

While the MVP focuses on core valuation frameworks (**Magic Formula**, **Bruce Greenwald EPV & Reproduction Cost**, **Steady-State DCF**), the architecture of `Value_Investing_Alpha` is deliberately decoupled so that additional SEC modules from `edgartools` can be mounted as modular API routers and terminal views without rewriting core logic.

```
                    ┌───────────────────────────────────┐
                    │      FastAPI Router Engine        │
                    └─────────────────┬─────────────────┘
                                      │
         ┌───────────────┬────────────┴───┬───────────────┬───────────────┐
         ▼               ▼                ▼               ▼               ▼
     [MVP Core]     [Module 1]       [Module 2]      [Module 3]      [Module 4]
   Fundamentals     Form 13F         Form 4          Form 8-K        DEF 14A
   Screener & EPV   Superinvestors   Insider Radar   Material Alerts Governance
```

---

## 2. Planned Features & edgartools Implementation

### Feature 1: Superinvestor Portfolio Tracker (Form 13F-HR)

**Value Investing Principle**:
Tracking what elite capital allocators (e.g., Warren Buffett, Li Lu, Mohnish Pabrai, Seth Klarman) are buying provides a rich source of validated investment ideas.

**edgartools API Integration**:
```python
import edgar

# Fetch Berkshire Hathaway 13F filings
cik = "0001067983"  # Berkshire Hathaway
company = edgar.Company(cik)
filing_13f = company.get_filings(form="13F-HR").latest()

# Extract holdings table
holdings = filing_13f.thirteenf()
holdings_df = holdings.holdings_data
```

**Terminal UI Component**:
- New **"SUPERINVESTORS"** tab in the top navigation.
- Table showing: Portfolio weighting, new additions, position increases, trimmed positions, and complete liquidations.

---

### Feature 2: Insider Trading & Cluster Buying Radar (Form 4)

**Value Investing Principle**:
*"Insiders might sell their shares for any number of reasons, but they only buy them for one: they think the price is going to go up."* — Peter Lynch.
Cluster purchases (3+ executives or directors buying stock with personal cash in a 30-day window) indicate high insider conviction.

**edgartools API Integration**:
```python
import edgar

company = edgar.Company("AAPL")
form4_filings = company.get_filings(form="4").latest(10)

for filing in form4_filings:
    ownership = filing.ownership()
    # Filter for Open Market Purchases (Transaction Code 'P')
    purchases = [
        tx for tx in ownership.transactions 
        if tx.transaction_code == "P" and tx.shares > 0
    ]
```

**Terminal UI Component**:
- In the Company Detail Drawer: **"INSIDER ACTIVITY"** panel.
- Badge indicators: "CLUSTER BUYING DETECTED" (highlighted in bright terminal green).

---

### Feature 3: Real-Time Material Events & Risk Monitor (Form 8-K)

**Value Investing Principle**:
Companies must file Form 8-K within 4 business days of major corporate events. Value investors need instant notifications of CEO resignations, debt covenant breaches, or material contract cancellations.

**edgartools API Integration**:
```python
import edgar

# Retrieve recent 8-K filings by Item category
company = edgar.Company("TXN")
eight_k_filings = company.get_filings(form="8-K").latest(5)

for filing in eight_k_filings:
    items = filing.items  # e.g., ['Item 5.02: Departure of Directors or Certain Officers']
    summary = filing.text()
```

**Terminal UI Component**:
- Header alert ticker: scrolling feed of 8-K filings for currently tracked universe.
- Classification tags: *Item 1.01 (Agreements)*, *Item 2.01 (Acquisitions)*, *Item 5.02 (Executive Changes)*.

---

### Feature 4: Executive Compensation & Shareholder Alignment (DEF 14A Proxy)

**Value Investing Principle**:
Charlie Munger frequently stressed: *"Show me the incentive and I will show you the outcome."*
We must evaluate whether management incentives are tied to return on capital (ROC) or merely revenue growth through dilution.

**edgartools API Integration**:
```python
import edgar

company = edgar.Company("MSFT")
proxy_filing = company.get_filings(form="DEF 14A").latest()

# Extract executive compensation tables and shareholder proposals
proxy_data = proxy_filing.proxy()
exec_comp_df = proxy_data.executive_compensation
```

**Terminal UI Component**:
- Detail Drawer Section: **"MANAGEMENT & INCENTIVES"**.
- Displays CEO/CFO Total Compensation, Stock Option Grants, and Performance Hurdles.

---

### Feature 5: Full-Text XBRL Footnote Search (`edgar_text_search`)

**Value Investing Principle**:
The most critical risks are buried in the footnotes of financial statements (operating leases, legal liabilities, pension underfunding, off-balance sheet obligations).

**edgartools API Integration**:
```python
import edgar

# Search across 10-K filings using BM25 keyword matching
company = edgar.Company("GOOGL")
ten_k = company.get_filings(form="10-K").latest()

# Search within MD&A or Notes
results = ten_k.search("material weakness in internal control", section="Item 8")
```

**Terminal UI Component**:
- Search bar inside the company drawer allowing direct full-text query of the 10-K with instant sentence highlight.

---

## 3. Implementation Phasing

| Phase | Target Module | Endpoints to Add | UI Panel |
| :--- | :--- | :--- | :--- |
| **Stage 2.1** | Form 4 Insider Radar | `GET /api/company/{ticker}/insider-trades` | Drawer Tab: Insider Purchases & Sales |
| **Stage 2.2** | Form 13F Superinvestors | `GET /api/superinvestors/all`, `GET /api/superinvestors/{cik}` | New Top Navigation: 13F Portfolios |
| **Stage 2.3** | Form 8-K Material Feeds | `GET /api/company/{ticker}/material-events` | Header Warning Ticker |
| **Stage 2.4** | DEF 14A Proxy Alignment | `GET /api/company/{ticker}/governance` | Drawer Tab: Executive Compensation |
| **Stage 2.5** | Footnote Full-Text Search | `POST /api/company/{ticker}/search-filing` | Interactive Search Modal |

All models will reuse our existing caching pipeline, `EDGAR_LOCAL_DATA_DIR` storage guardrails, and asynchronous FastAPI structures.
