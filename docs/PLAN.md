# Value Investing Alpha - Project Master Plan & Roadmap

## Overview & Approach Selection

- **Selected Architecture**: **Approach 3 (Possibility 1)** from `docs/WEB_APP_PROPOSALS.md`.
- **Backend**: FastAPI on Python 3.13, wrapping fundamental SEC XBRL data (`edgartools`) and market data (`yfinance`).
- **Frontend**: High-density "Bloomberg Terminal" aesthetic web UI built with React, Vite, Tailwind CSS, and JetBrains Mono monospace font.
- **Deployment**: Google Cloud Run (containerized, scale-to-zero for zero idle cost, covered by GCP free tier / credits).
- **Quota-Friendly Execution**: The project is partitioned into 5 independent chunks, each runnable in a single session within Gemini free weekly quotas.

---

## Roadmap Chunks

```
Chunk 1: Project Scaffolding, Environment & GitHub Setup   [COMPLETED]
Chunk 2: Backend API Development & Engine Integration     [COMPLETED]
Chunk 3: Terminal Web Frontend (Bloomberg Aesthetic)      [COMPLETED]
Chunk 4: Company Deep-Dive, Charts & Export Features      [COMPLETED]
Chunk 5: Docker Containerization & Cloud Run Hosting      [COMPLETED]
Chunk 6: Auth, Real-Data Live Testing & SSD Engine Run    [COMPLETED]
Chunk 7: Storage Resilience & Data Folder Reconciliation  [COMPLETED]
Chunk 8: SEC Filing Reader & Redline Table Rendering      [COMPLETED]
Chunk 9: Stage 2 - Superinvestors (13F) & Form 4 Radar    [COMPLETED]
Chunk 10: Stage 2 - Form 8-K, DEF 14A & Full-Text Search  [COMPLETED]
Chunk 11: Mac/Windows README, Docs Audit & Final Commit   [COMPLETED]
```

---

### Chunk 1: Foundation, Workspace & GitHub Setup (Completed / In Progress)

- [X] Analyze `Value_Investing_Screener_SEC_Market_Data` and `WEB_APP_PROPOSALS.md`.
- [X] Migrate core calculation models, SEC providers, market data sync, and tests to `Value_Investing_Alpha`.
- [X] Import key skills from `antigravity-awesome-skills` (`data-dense-design`, `fastapi-pro`, `fastapi-router-py`, `git-workflow`).
- [X] Create workspace customization configuration (`.agents/mcp_config.json`).
- [X] Create `GEMINI.md` foundational instructions and operational guidelines.
- [X] Configure `.env.example`, `.gitignore`, and updated `requirements.txt`.
- [X] Scaffold initial FastAPI application structure (`src/api/`).
- [X] Initialize local Git repository with baseline commit (`main`).
- [X] Create and activate Python 3.13 virtual environment (`.venv`) and install all 107 dependencies.
- [X] Verify unit test suite (14 passed, 6 skipped, 0 failures).
- [X] Connect remote GitHub repository (`gh auth login` & `gh repo create`).
- [X] Set `GITHUB_PERSONAL_ACCESS_TOKEN` in `.env` for GitHub MCP integration.

---

### Chunk 2: Backend API Endpoints & Engine Wrapping (Completed)

- [x] Build Pydantic schemas in `src/api/schemas/screener.py` and `src/api/schemas/company.py` for screener queries and results.
- [x] Implement `src/api/routes/screener.py`:
  - `GET /api/screener/results`: Fetch cached or latest screened stocks with sort, limit, and SIC filtering.
  - `POST /api/screener/run`: Run screener with configurable filters (market cap min/max, sector, model weights).
- [x] Implement `src/api/routes/company.py`:
  - `GET /api/company/{ticker}`: Detailed financial facts, Magic Formula ranking, EPV vs Reproduction cost analysis, and DCF steady-state value.
  - `GET /api/company/{ticker}/sec-facts`: Direct SEC entity facts lookup.
- [x] Establish typed dependency injection in `src/api/deps.py`.
- [x] Mount modular routers in `src/api/main.py`.
- [x] Write API tests using `fastapi.testclient.TestClient` and `pytest` (19 passing overall).

---

### Chunk 3: Frontend Terminal UI (React + Vite) (Completed)

- [x] Initialize Vite + React + TypeScript in `frontend/`.
- [x] Install Tailwind CSS and configure the Data-Dense theme (JetBrains Mono, dark background `#0a0c10`, panel `#10141a`, border `#232936`, neon green `#00e676` / amber accents).
- [x] Implement Dense Data Table (`data-dense-design` pattern):
  - Column sorting (Rank, Ticker, Company, Sector, Price, Market Cap, EV, EBIT, Earnings Yield, Return on Capital, Reproduction Value / sh, EPV / sh, EPV MOS, Solvency).
  - Quick text filtering by ticker/company name.
  - Sector filtering buttons and Market Cap minimum threshold selector.
  - Muted red/green visual badges for valuation premiums/discounts and solvency traffic lights.
- [x] Implement slide-over Company Detail Drawer (`CompanyDrawer.tsx`):
  - Deep-dive breakdown of Greenblatt's Magic Formula.
  - Bruce Greenwald EPV vs. Reproduction Cost (franchise moat factor).
  - Steady-state DCF valuation.
  - Solvency & Working capital anomaly checks.
  - Full raw SEC XBRL statement data viewer.
- [x] Build production bundle via `npm run build` and mount static distribution in FastAPI `src/api/main.py`.

---

### Chunk 4: Deep-Dive Views & Reporting (Completed)

- [x] Implement company detail drawer sensitivity matrices:
  - EPV Hurdle Rate Sensitivity Table (varying WACC 8% to 12%).
  - 2D DCF Sensitivity Grid (varying discount rates 8% to 10% vs perpetual growth 1.5% to 2.5%).
  - Franchise Moat indicator ($>1.0\times$ EPV to Reproduction Cost).
- [x] Add CSV and Excel export endpoints in FastAPI (`/api/screener/export/csv`, `/api/screener/export/excel`).
- [x] Connect Export CSV and Export Excel triggers to frontend Toolbar.
- [x] Add cache & storage health telemetry in UI header consuming `/health/storage`.
- [x] Write automated tests for export endpoints and cache status (22 tests passing).

---

### Chunk 5: Containerization & Cloud Run Hosting Guide (Completed)

- [x] Build multi-stage `Dockerfile`:
  - Stage 1: Build React static assets via `node:22-alpine` (`npm run build`).
  - Stage 2: `python:3.13-slim` image with FastAPI, SEC tools, and compiled frontend static mount.
- [x] Create `.dockerignore` to keep image minimal and clean.
- [x] Author comprehensive, beginner-friendly cloud deployment guide:
  - [docs/CLOUD_RUN_HOSTING_GUIDE.md](file:///Users/gabrielepicheo/Documents/Github/gp1981/Value_Investing_Alpha/docs/CLOUD_RUN_HOSTING_GUIDE.md) detailing $300 GCP credit activation, scale-to-zero ($0/month), and one-command deployment.
- [x] Author technical architecture guide for non-professionals:
  - [docs/ARCHITECTURE.md](file:///Users/gabrielepicheo/Documents/Github/gp1981/Value_Investing_Alpha/docs/ARCHITECTURE.md) covering tech stack, user experience lifecycle, memory/cache mechanics, and valuation formulas.
- [x] Author Stage 2 extensibility roadmap:
  - [docs/STAGE_2_EDGARTOOLS_ROADMAP.md](file:///Users/gabrielepicheo/Documents/Github/gp1981/Value_Investing_Alpha/docs/STAGE_2_EDGARTOOLS_ROADMAP.md) detailing post-MVP Form 13F, Form 4 insider cluster buying, Form 8-K material events, and DEF 14A proxy alignment.

---

### Chunk 6: Auth, Real-Data Live Testing & SSD Engine Run (Completed)

- [x] Remove erroneous "CAGR Full Equity w/ Debt (%)" metric across models, export pipelines, and methodology documentation.
- [x] Implement lightweight JWT user authentication:
  - Backend: salted PBKDF2 HMAC-SHA256 password hashing, HS-256 JWT tokens, pre-seeded demo account (`analyst@example.com` / `valuealpha2026`), endpoints `/api/auth/register`, `/api/auth/login`, `/api/auth/me`.
  - Frontend: `AuthModal.tsx` modal, `Header.tsx` displaying user email and tier status.
  - Zero-cost cloud auth strategy documented in `docs/CLOUD_RUN_HOSTING_GUIDE.md` (Firebase Auth / Supabase Auth free tiers).
- [x] Run live end-to-end screener test fetching real SEC data to external SSD (`/Volumes/T3/edgartools`).
- [x] Verify web terminal live data visualization, company drawer, and export features.

---

### Chunk 7: Storage Resilience & Data Folder Reconciliation (In Progress)

- [ ] Fix `PermissionError` in `src/api/main.py` and `SECProvider` when external SSD (`/Volumes/T3`) is disconnected: detect unreachable/unmounted paths and gracefully fall back to local `output/` + live on-demand SEC fetching.
- [ ] Reconcile duplicate `output/data/` and `output/data/data/` directories into a single canonical `output/` layout (`output/company_data.csv`, `output/users.json`, `output/edgar_data/`, `output/edgar_cache/`).
- [ ] Ensure `company_data.csv` loads cleanly without T3 attached, while `CompanyDrawer` fetches missing filings/facts live from SEC on-demand with in-memory caching.

---

### Chunk 8: SEC Filing Reader & Redline Table Rendering (Pending)

- [ ] Complete manual drag-resize handle in `CompanyDrawer.tsx` (50% default width + smooth drag).
- [ ] Upgrade `SEC Filing Reader` backend & UI:
  - Period presets (Last Quarter, Last 4 Quarters, Last Year, Last 5 Years, Date Range) & Form Type dropdown with edgartools data-object descriptions.
  - Scrollable filing list + Attachments links panel.
  - Full section descriptions (`Item 1 - Business`, `Item 1A - Risk Factors`, etc.) as clickable sidebar bookmarks.
  - Structured table/markdown rendering for 10-K/10-Q/8-K content and Redline Diff.

---

### Chunk 9: Stage 2 — Superinvestors (13F) & Form 4 Insider Radar (Pending)

- [ ] Build `src/api/routes/superinvestors.py` with curated Value Superinvestor roster (Buffett, Klarman, Li Lu, Pabrai, Marks, Greenblatt, Ackman, Einhorn, Watsa, Akre, Gayner, Tweedy Browne).
- [ ] Implement `GET /api/superinvestors/list` and `GET /api/superinvestors/{cik}` with 13F-HR holdings, weights, and QoQ activity.
- [ ] Add top-level `SUPERINVESTORS (13F)` view in React frontend.
- [ ] Implement `GET /api/company/{ticker}/insider-trades` (Form 4) with 30-day Cluster Buying detection and `INSIDER RADAR` drawer tab.

---

### Chunk 10: Stage 2 — Form 8-K Material Events, DEF 14A Governance & Full-Text Search (Pending)

- [ ] Implement `GET /api/company/{ticker}/material-events` (Form 8-K item classification).
- [ ] Implement `GET /api/company/{ticker}/governance` (DEF 14A proxy executive compensation & alignment).
- [ ] Implement `POST /api/company/{ticker}/search-filing` (10-K section/keyword search).
- [ ] Integrate 8-K, DEF 14A, and Search UI into `CompanyDrawer.tsx`.

---

### Chunk 11: Mac/Windows README, Docs Audit & Final Commit (Pending)

- [ ] Update `README.md` with full Mac & Windows local installation, T3 vs live SEC mode, and troubleshooting.
- [ ] Update `docs/ARCHITECTURE.md` and `docs/CLOUD_RUN_HOSTING_GUIDE.md` for canonical storage and Stage 2 modules.
- [ ] Update `docs/LOGS/SESSION_LOG.md`, run full `pytest` + `npm run build`, and commit cleanly.
