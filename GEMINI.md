# GEMINI.md - Value Investing Alpha

## Foundational Mandates

- **Contextual Precedence**: This file is the primary source of truth for Gemini / Antigravity agents working in this repository.
- **Project Vision**: Value Investing Alpha is a web platform and terminal interface combining SEC XBRL filings (`edgartools`) and market data (`yfinance`) with rigorous fundamental models:
  1. **Magic Formula (Joel Greenblatt)**: Earnings Yield & Return on Capital.
  2. **Reproduction Cost & Earning Power Value (Bruce Greenwald)**: Balance sheet reproduction vs. normalized earnings.
  3. **Discounted Cash Flow (DCF)**: Steady-state cash flow valuation.
- **Architecture (Approach 3 - Serverless Terminal API)**:
  - **Backend**: FastAPI REST & streaming API (`src/api/`).
  - **Core Engine**: Financial models (`src/models/`), SEC & Market integrations (`src/data/`), screener pipeline (`src/engine/`).
  - **Frontend**: Data-dense terminal web interface (`frontend/`) using React, Vite, Tailwind, JetBrains Mono font, dark mode with neon accents (Bloomberg Terminal aesthetic).
  - **Target Hosting**: Containerized on Google Cloud Run (scale-to-zero, free-tier friendly).
- **Security**: Never expose API keys or secrets. Store sensitive values in `.env` (gitignored). Always provide `.env.example`.
- **Environment & SSD Protection**: Always ensure `EDGAR_LOCAL_DATA_DIR` and `EDGAR_CACHE_DIR` are configured (e.g. external SSD or dedicated local folder) before batch downloads to prevent SSD exhaustion.

---

## Core Workflows & Antigravity Agent Protocol

### Session Startup Protocol
1. Check `docs/PLAN.md` to identify the current milestone chunk and active task.
2. Check `docs/LOGS/SESSION_LOG.md` for the context and handoff notes from the previous session.
3. Verify environment prerequisites before running tests or dev servers.

### Session Handoff & Conclusion Protocol
When a chunk is completed or the session is concluding:
1. Update `docs/PLAN.md` with completed items and current status.
2. Record a structured entry in `docs/LOGS/SESSION_LOG.md` (what was done, files touched, current state, next immediate step for the next agent).
3. If new rules, dependencies, or architectural decisions were introduced, update `GEMINI.md`.
4. Run tests (`pytest`) to ensure no regressions.
5. Provide a clear commit message for Git.

### Development Standards
- **Data Integrity**: Prioritize SEC XBRL filings (`edgartools`) over commercial APIs. Use `yfinance` primarily for real-time market cap, price, and beta.
- **Data-Dense Design**: Adhere to the `data-dense-design` skill guidelines for the UI: compact layouts (2-4px padding), monospace numbers, tabular alignment, high information density, muted red/green delta highlights.
- **FastAPI Standards**: Follow `fastapi-pro` patterns: Pydantic V2 schemas, async endpoints, modular APIRouter structure, OpenAPI tags, typed dependencies.
- **Testing**: Maintain tests in `tests/`. Run `pytest tests/` regularly.

---

## Workspace Structure

```
Value_Investing_Alpha/
├── GEMINI.md                    # Agent instructions and rules
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
├── .gitignore                   # Git ignore patterns
├── .agents/
│   ├── mcp_config.json          # MCP configuration (GitHub, Edgar)
│   └── skills/                  # Localized workspace skills
│       ├── data-dense-design/   # Bloomberg UI design system
│       ├── fastapi-pro/         # FastAPI production guide
│       ├── fastapi-router-py/   # Route best practices
│       └── git-workflow/        # Git and GitHub best practices
├── src/
│   ├── api/                     # FastAPI backend
│   │   ├── main.py              # App entrypoint
│   │   ├── routes/              # Modular API endpoints
│   │   └── schemas/             # Pydantic models
│   ├── data/                    # SEC and market data providers
│   ├── engine/                  # Screener, filter, and integration
│   ├── models/                  # Financial valuation algorithms
│   └── utils/                   # Cache, formatting, export utils
├── frontend/                    # React + Vite terminal interface
├── docs/
│   ├── PLAN.md                  # Milestone & chunk roadmap
│   ├── METHODOLOGY.md           # Valuation mathematics & logic
│   ├── BRD.md                   # Business requirements
│   ├── WEB_APP_PROPOSALS.md     # Architecture proposals
│   └── LOGS/
│       └── SESSION_LOG.md       # Session-by-session history & handoff
├── tests/                       # Unit and integration tests
└── references/                  # Value investing literature & research
```
