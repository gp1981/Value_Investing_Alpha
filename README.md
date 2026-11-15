# Value Investing Alpha 📊🏛️

> **High-Integrity Fundamental Screener & Bloomberg-Style Web Terminal**  
> Direct SEC XBRL Filings (`edgartools`) • Live Market Data (`yfinance`) • Rigorous Academic Valuation Models

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python 3.13](https://img.shields.io/badge/Python-3.13+-3776AB.svg?style=flat&logo=python)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style](https://img.shields.io/badge/Code%20Style-Data--Dense-blueviolet.svg)](#terminal-design)

---

## 📌 Repository About & Metadata

- **Short Description**: High-integrity value investing screener & Bloomberg-style terminal web app combining SEC XBRL filings (`edgartools`) with Magic Formula, Greenwald EPV, and DCF models.
- **Website / Demo**: Containerized on Google Cloud Run (Serverless, scale-to-zero).
- **GitHub Topics**: `value-investing`, `stock-screener`, `sec-edgar`, `xbrl`, `magic-formula`, `earning-power-value`, `fastapi`, `react`, `bloomberg-terminal`, `financial-analysis`

---

## 💡 What is Value Investing Alpha?

Most stock screeners rely on third-party commercial APIs that obscure financial reporting footnotes, aggregate line items inconsistently, or fail to adjust for capital structures.

**Value Investing Alpha** builds fundamental analysis from the primary source of truth: **official SEC XBRL 10-K and 10-Q filings**. It combines this raw financial reporting with real-time market data to execute three classic value investing valuation frameworks:

1. **Joel Greenblatt's Magic Formula**:
   - **Earnings Yield**: $\text{EBIT} / \text{Enterprise Value}$
   - **Return on Capital (ROC)**: $\text{EBIT} / (\text{Net Working Capital} + \text{Net Fixed Assets})$
2. **Bruce Greenwald's Asset Reproduction Cost & Earning Power Value (EPV)**:
   - **Reproduction Cost**: Balance sheet line-by-line adjustment (cash, accounts receivable, inventory haircuts, PP&E replacement, intangible adjustments).
   - **Earning Power Value (EPV)**: Normalized steady-state EBIT after maintenance CapEx and structural taxes, capitalized at the cost of capital.
   - **Franchise / Moat Evaluation**: EPV compared against Reproduction Cost to identify structural economic moats.
3. **Discounted Cash Flow (DCF)**:
   - Conservative steady-state projection based on normalized owner earnings.

---

## 🏛️ System Architecture (Approach 3: Serverless Terminal API)

```
Value_Investing_Alpha/
├── src/
│   ├── api/                     # FastAPI async backend
│   │   ├── main.py              # Application entrypoint & CORS
│   │   ├── routes/              # Endpoints (/health, /api/screener, /api/company)
│   │   └── schemas/             # Pydantic validation models
│   ├── engine/                  # Screener pipeline & filtering
│   │   ├── filter.py            # SIC industry, ADR, market cap filters
│   │   ├── integrator.py        # Data orchestration & merging
│   │   └── screener.py          # Ranking and composite scoring
│   ├── models/                  # Core financial algorithms
│   │   ├── magic_formula.py     # Earnings Yield & ROC calculations
│   │   ├── greenwald.py         # Reproduction Cost & EPV
│   │   ├── dcf.py               # DCF valuation engine
│   │   └── safety.py            # Altman Z-Score & Beneish M-Score checks
│   ├── data/                    # SEC XBRL & Yahoo Finance providers
│   │   ├── sec_provider.py      # edgartools client with cascading fallbacks
│   │   └── market_provider.py   # yfinance client for market cap and prices
│   └── utils/                   # Cache managers, Excel exports, formatters
├── frontend/                    # React + Vite data-dense terminal interface
├── docs/                        # Specifications, plans, and session logs
│   ├── PLAN.md                  # 5-chunk delivery roadmap
│   ├── METHODOLOGY.md           # Valuation mathematics & XBRL mappings
│   └── LOGS/                    # Multi-agent handoff logs
├── tests/                       # Unit and integration test suite
└── .agents/                     # Antigravity agent skills and MCP tools
```

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.12+ (Python 3.13 recommended)
- `uv` (recommended fast package manager) or standard `pip`
- Node.js 20+ (for frontend development)

### 1. Clone & Set Up Virtual Environment

```bash
git clone https://github.com/gp1981/Value_Investing_Alpha.git
cd Value_Investing_Alpha

# Create virtual environment using uv
uv venv .venv --python python3.13

# Activate virtual environment
source .venv/bin/activate

# Install all dependencies
uv pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` to declare your identity for SEC EDGAR (required by the SEC fair-access policy):
```env
EDGAR_IDENTITY="Your Name your.email@example.com"
EDGAR_LOCAL_DATA_DIR="/Volumes/T3/edgartools"  # Optional: external drive to preserve SSD
```

### 3. Run Backend API

```bash
# Start FastAPI backend with hot-reload
uvicorn src.api.main:app --reload --port 8000
```
Open [http://localhost:8000/docs](http://localhost:8000/docs) to explore the interactive Swagger API documentation.

### 4. Run Unit Tests

```bash
pytest tests/
```

---

## 🖥️ Terminal Web Interface (Bloomberg Aesthetic)

The frontend is built according to the **Data-Dense Design** philosophy:
- **Zero-Waste Density**: Compact row padding (2-4px) to maximize visible financial metrics without scrolling.
- **Monospace Alignment**: `JetBrains Mono` tabular figures for instant visual scanning of millions vs billions.
- **Muted Contrast**: Dark IDE slate palette (`#121212`) with subdued neon accents (terminal green, amber warnings, muted red discounts).

---

## 🗺️ Project Delivery Roadmap

| Chunk | Scope | Status |
| :--- | :--- | :--- |
| **Chunk 1** | Scaffolding, Migration, MCP & Environment Configuration | ✅ Completed |
| **Chunk 2** | FastAPI Backend Endpoints (`/screener`, `/company/{ticker}`) | 🟡 In Progress |
| **Chunk 3** | React + Vite Data-Dense Terminal Frontend | ⏳ Upcoming |
| **Chunk 4** | Interactive Visuals (EPV vs Reproduction, DCF Matrix, Excel Export) | ⏳ Upcoming |
| **Chunk 5** | Containerization & Cloud Run Deployment Guide | ⏳ Upcoming |

---

## 📄 License & Attribution

Distributed under the MIT License. Financial models derived from:
- *The Little Book That Still Beats the Market* (Joel Greenblatt)
- *Value Investing: From Graham to Buffett and Beyond* (Bruce Greenwald et al.)
