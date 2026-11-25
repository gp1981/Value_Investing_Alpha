# Value Investing Alpha 📊🏛️

> **High-Integrity Fundamental Screener & Bloomberg-Style Web Terminal**  
> Direct SEC XBRL Filings (`edgartools`) • Live Market Data (`yfinance`) • Rigorous Academic Valuation Models

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python 3.13](https://img.shields.io/badge/Python-3.13+-3776AB.svg?style=flat&logo=python)](https://www.python.org/)
[![React 18](https://img.shields.io/badge/React-18.3-61DAFB.svg?style=flat&logo=react)](https://react.dev/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4-38B2AC.svg?style=flat&logo=tailwindcss)](https://tailwindcss.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style](https://img.shields.io/badge/Code%20Style-Data--Dense-blueviolet.svg)](#terminal-design)

---

## 📌 Repository About & Metadata

- **Short Description**: High-integrity value investing screener & Bloomberg-style terminal web app combining SEC XBRL filings (`edgartools`) with Magic Formula, Greenwald EPV, and DCF models.
- **Website / Deployment**: Containerized on Google Cloud Run (Serverless, scale-to-zero, $0 idle cost).
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
   - **Earning Power Value (EPV)**: Normalized steady-state EBIT after maintenance CapEx and structural taxes, capitalized at the cost of capital ($WACC$).
   - **Franchise / Moat Evaluation**: EPV compared against Reproduction Cost to identify structural economic moats.
3. **Discounted Cash Flow (DCF)**:
   - Conservative steady-state projection based on normalized owner earnings.

---

## 🏛️ System Architecture (Approach 3: Serverless Terminal API)

```
Value_Investing_Alpha/
├── src/
│   ├── api/                     # FastAPI async backend
│   │   ├── main.py              # Application entrypoint, CORS & static frontend mount
│   │   ├── deps.py              # Dependency injection provider
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
│   ├── src/
│   │   ├── components/          # Header, Toolbar, ScreenerTable, CompanyDrawer
│   │   ├── App.tsx              # Application coordinator & state
│   │   └── types.ts             # TypeScript interface contracts
│   └── dist/                    # Compiled production assets
├── docs/                        # Specifications, plans, and session logs
│   ├── ARCHITECTURE.md          # Comprehensive technical guide for non-professionals
│   ├── CLOUD_RUN_HOSTING_GUIDE.md # Step-by-step $300 GCP credit deployment guide
│   ├── STAGE_2_EDGARTOOLS_ROADMAP.md # Post-MVP edgartools feature expansion
│   ├── PLAN.md                  # 5-chunk delivery roadmap
│   ├── METHODOLOGY.md           # Valuation mathematics & XBRL mappings
│   └── LOGS/                    # Multi-agent session history
├── tests/                       # Unit and integration test suite (22 tests passing)
├── Dockerfile                   # Multi-stage production container build
└── .agents/                     # Antigravity agent skills and MCP tools
```

---

## 🚀 Running the Platform Locally (macOS & Windows)

### Prerequisites
- **Python 3.12+** (Python 3.13 recommended)
- **Node.js 20+** (for frontend compilation)
- **`uv`** (optional, ultra-fast Python package manager) or standard `pip`

### Canonical Data & Storage Layout
- `output/company_data.csv` — Screener dataset (served immediately on startup, even without external storage).
- `output/users.json` — Local authentication store.
- `output/edgar_data/` & `output/edgar_cache/` — Automatic local fallback when `EDGAR_LOCAL_DATA_DIR` (e.g. an external SSD like `/Volumes/T3/edgartools`) is disconnected; missing filings are fetched live from SEC EDGAR on demand and cached in memory.

---

### Option A: macOS Setup & Run

```bash
# 1. Install prerequisites (if needed)
brew install python@3.13 node uv

# 2. Clone repository
git clone https://github.com/gp1981/Value_Investing_Alpha.git
cd Value_Investing_Alpha

# 3. Create virtual environment & install dependencies
uv venv .venv --python python3.13
source .venv/bin/activate
uv pip install -r requirements.txt

# 4. Configure SEC identity (required by SEC EDGAR)
cp .env.example .env
# Edit .env and set EDGAR_IDENTITY="Your Name your.email@example.com"
# Optional: set EDGAR_LOCAL_DATA_DIR="/Volumes/T3/edgartools" (falls back automatically if unplugged)

# 5. Build the frontend assets
cd frontend
npm install
npm run build
cd ..

# 6. Start the unified terminal server
uvicorn src.api.main:app --port 8000
```

---

### Option B: Windows (PowerShell) Setup & Run

```powershell
# 1. Install Python 3.13 (python.org) and Node.js 20+ (nodejs.org), then open PowerShell

# 2. Clone repository
git clone https://github.com/gp1981/Value_Investing_Alpha.git
cd Value_Investing_Alpha

# 3. Create virtual environment & install dependencies
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 4. Configure SEC identity
Copy-Item .env.example .env
# Open .env in Notepad and set EDGAR_IDENTITY="Your Name your.email@example.com"
# Optional: set EDGAR_LOCAL_DATA_DIR="D:\edgartools" (falls back automatically if unplugged)

# 5. Build the frontend assets
cd frontend
npm install
npm run build
cd ..

# 6. Start the unified terminal server
uvicorn src.api.main:app --port 8000
```

Open your browser to:
- **Terminal Web App**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### Option B: Split Development Mode (Hot-Reloading for Code Editing)

If you are modifying code in React or FastAPI and want instant live-reload:

**Terminal Window 1 (Backend API)**:
```bash
source .venv/bin/activate
uvicorn src.api.main:app --reload --port 8000
```

**Terminal Window 2 (React Vite Frontend)**:
```bash
cd frontend
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) to view the terminal with instant Vite hot-module replacement.

---

## 🧪 Running Automated Tests

To run the complete test suite:
```bash
source .venv/bin/activate
pytest tests/
```
*Current test suite: **22 passed, 6 skipped, 0 failures**.*

---

## 📊 Exporting Data & Reports

You can download screener data directly from the web interface or via the API:
- **Download CSV**: Click the **CSV** button in the toolbar, or visit [http://localhost:8000/api/screener/export/csv](http://localhost:8000/api/screener/export/csv).
- **Download Formatted Excel**: Click the **EXCEL** button in the toolbar, or visit [http://localhost:8000/api/screener/export/excel](http://localhost:8000/api/screener/export/excel).

---

## ☁️ Deploying to Google Cloud Run ($300 Credit)

The platform is designed for **scale-to-zero** containerized execution on Google Cloud Run. When nobody is using the site, it idles at **\$0.00 / month**, meaning your \$300 Google Cloud credit will cover hosting indefinitely.

For the complete, beginner-friendly step-by-step setup guide, see:  
👉 **[docs/CLOUD_RUN_HOSTING_GUIDE.md](file:///Users/gabrielepicheo/Documents/Github/gp1981/Value_Investing_Alpha/docs/CLOUD_RUN_HOSTING_GUIDE.md)**

---

## 📚 Technical & Architecture Documentation

For an in-depth understanding of how the platform mechanics, memory caching, and financial formulas work:
- 📖 **[docs/ARCHITECTURE.md](file:///Users/gabrielepicheo/Documents/Github/gp1981/Value_Investing_Alpha/docs/ARCHITECTURE.md)**: Explains what each technology is for, walks through the user experience, details how cache and SSD protection work, and provides the mathematical logic of the valuation models.
- 🔭 **[docs/STAGE_2_EDGARTOOLS_ROADMAP.md](file:///Users/gabrielepicheo/Documents/Github/gp1981/Value_Investing_Alpha/docs/STAGE_2_EDGARTOOLS_ROADMAP.md)**: Details the post-MVP plan to integrate advanced `edgartools` capabilities, including Form 13F Superinvestor tracking, Form 4 Insider Cluster Buying radar, Form 8-K material event feeds, and DEF 14A proxy alignment audits.
- 📋 **[docs/PLAN.md](file:///Users/gabrielepicheo/Documents/Github/gp1981/Value_Investing_Alpha/docs/PLAN.md)**: Project milestone and chunk delivery status.
- 📝 **[docs/LOGS/SESSION_LOG.md](file:///Users/gabrielepicheo/Documents/Github/gp1981/Value_Investing_Alpha/docs/LOGS/SESSION_LOG.md)**: Session-by-session engineering logs and multi-agent handoff notes.

---

## 📄 License & Attribution

Distributed under the MIT License. Valuation models derived from:
- *The Little Book That Still Beats the Market* (Joel Greenblatt)
- *Value Investing: From Graham to Buffett and Beyond* (Bruce Greenwald et al.)
- SEC filing tools powered by [edgartools](https://github.com/dgunning/edgartools) by Dwight Gunning.
