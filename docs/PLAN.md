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
Chunk 1: Project Scaffolding, Environment & GitHub Setup   [IN PROGRESS / TODAY]
Chunk 2: Backend API Development & Engine Integration     [PLANNED]
Chunk 3: Terminal Web Frontend (Bloomberg Aesthetic)      [PLANNED]
Chunk 4: Company Deep-Dive, Charts & Export Features      [PLANNED]
Chunk 5: Docker Containerization & Cloud Run Hosting      [PLANNED]
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

### Chunk 3: Frontend Terminal UI (React + Vite)

- [ ] Initialize Vite + React + TypeScript in `frontend/`.
- [ ] Install Tailwind CSS and configure the Data-Dense theme (JetBrains Mono, dark background `#121212`, border `#2a2a2a`, neon green `#00ff66` / amber accents).
- [ ] Implement Dense Data Table (`data-dense-design` pattern):
  - Column sorting, filtering by market cap, sector, earnings yield, ROC.
  - Muted red/green visual badges for valuation premiums/discounts.
- [ ] Add top ticker status bar and command palette.
- [ ] Connect frontend to FastAPI `/api/screener/results`.

---

### Chunk 4: Deep-Dive Views & Reporting

- [ ] Implement company detail drawer / modal with:
  - Reproduction Cost breakdown (Cash, Receivables, Inventory, PP&E, Intangibles).
  - Earning Power Value (EPV) calculation walkthrough.
  - Magic Formula rank factors.
- [ ] Add CSV and Excel export triggers (`src/utils/excel_exporter.py`).
- [ ] Add cache health indicator in UI header.

---

### Chunk 5: Containerization & Cloud Run Deployment

- [ ] Build multi-stage `Dockerfile`:
  - Stage 1: Build React static assets (`npm run build`).
  - Stage 2: Python 3.13 slim image with FastAPI and compiled frontend assets served via static mount.
- [ ] Create `.dockerignore`.
- [ ] Step-by-step GCP Cloud Run deployment guide and gcloud commands.
- [ ] Configure environment variables in Cloud Run console (`EDGAR_IDENTITY`, etc.).
- [ ] End-to-end cloud verification.
