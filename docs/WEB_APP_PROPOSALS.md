# Value Investing Screener: Project Summary & Web App Proposals

## 1. Project Summary (Validation)

Based on my research, the **Value Investing Screener** is a professional-grade fundamental analysis tool designed to identify undervalued stocks using three core frameworks:
1.  **Magic Formula (Greenblatt)**: Ranks companies by Earnings Yield and Return on Capital.
2.  **Asset Reproduction & EPV (Greenwald)**: Compares reproduction costs vs. normalized earning power.
3.  **DCF Analysis**: Projects steady-state free cash flows to estimate intrinsic value.

**Key Technical Differentiators:**
*   **High-Integrity Data**: Prioritizes SEC XBRL filings via `edgartools` over commercial APIs.
*   **Industrial EBIT Logic**: Uses cascading fallbacks to accurately calculate EBIT for complex corporate structures.
*   **TTM Normalization**: Standardizes fiscal data into 12-month trailing units regardless of filing frequency.
*   **Industry Context**: Calculates industry-specific cash requirements (SIC medians) to refine "Excess Cash" assumptions.
*   **Efficiency**: Features a persistence-first design using local CSV caching for rapid iteration and benchmarking.

---

## 2. Web App Architecture Proposals

Below are 5 approaches to bringing this screener to the web, balancing your 300$ GCP credit, desire for zero/low cost, and the "Bloomberg Terminal" aesthetic.

### Approach 1: Static "GitOps" Dashboard (Lowest Cost)
**Vibe:** Minimalist, fast, zero-server maintenance.
*   **Possibility 1 (As is):** A GitHub Action runs the current script weekly, saves `company_data.csv` to the repo, and triggers a build. A simple HTML/JS page (hosted on GitHub Pages) uses a library like **Tabulator** with a dark "Midnight" theme to load the CSV and provide filtering/sorting.
*   **Possibility 2 (Best Practices):** Use a Static Site Generator (Next.js or Vite). Convert the CSV to a search-optimized JSON. Use **FlexSearch** for instant client-side filtering. **Login:** Use GitHub authentication or a simple password-protected static gate (e.g., Static-Auth).
*   **Cost:** $0.
*   **Difficulty:** Low.

### Approach 2: Streamlit Cloud (Fastest Time-to-Web)
**Vibe:** Data science dashboard, interactive.
*   **Possibility 1 (As is):** Create a 50-line `app.py` that imports your existing `Screener` and `DataIntegrator`. User inputs tickers or cap thresholds via the UI. Deploy directly to **Streamlit Cloud** for free.
*   **Possibility 2 (Best Practices):** Deploy on **GCP Cloud Run** using your credits for higher performance. Add **Firebase Auth** (Free tier) for user login. Use **Redis (GCP Memorystore)** to cache SEC filing results across different users' sessions to stay under SEC rate limits.
*   **Cost:** $0 (Streamlit) or ~$5/mo (GCP credits cover this for years).
*   **Difficulty:** Very Low.

### Approach 3: Serverless Terminal API (The "Bloomberg" Vibe)
**Vibe:** Dark mode, command-line style web interface.
*   **Possibility 1 (As is):** Wrap `main.py` in a **FastAPI** wrapper. Deploy as a **GCP Cloud Function**. The frontend is a single-page React app using a "Terminal" CSS framework. It calls the function to get the latest rankings.
*   **Possibility 2 (Best Practices):** Use **Xterm.js** on the frontend to create a *real* terminal in the browser. The backend streams the CLI output (including the `tabulate` tables) to the web via **WebSockets**. Users type commands like `screen --limit 50 --sort epv`.
*   **Cost:** ~$0-2/mo (GCP Free Tier + Credits).
*   **Difficulty:** Medium.

### Approach 4: Managed Backend with Database (Scaling & History)
**Vibe:** Professional SaaS.
*   **Possibility 1 (As is):** The script runs in a docker container on **GCP Cloud Run**. It writes results to a **GCP Cloud Storage** bucket as CSVs. A frontend reads these CSVs via a signed URL.
*   **Possibility 2 (Best Practices):** Store results in a **Serverless PostgreSQL (Neon.tech - Free)** or **GCP Cloud SQL**. This allows for "Historical Slicing" (e.g., "Show me companies that have been in the top 10 for 4 weeks"). Use **Google Identity Platform** for industrial-grade login.
*   **Cost:** ~$0 (using Neon free tier + GCP credits).
*   **Difficulty:** High.

### Approach 5: No-Code "Terminal" (Google Sheets + AppSheet)
**Vibe:** Integration with your existing spreadsheet workflow.
*   **Possibility 1 (As is):** Modify the script to use the `gspread` library to write results directly into a **Google Sheet**. Share the sheet as "Read Only" for users.
*   **Possibility 2 (Best Practices):** Use **AppSheet** (connected to the Google Sheet) to generate a web/mobile UI. You can customize AppSheet with a dark "Terminal" theme. **Login:** Handled automatically by Google/AppSheet. Use **GCP Cloud Scheduler** to trigger the Python script weekly.
*   **Cost:** $0 (included with many Google Workspace accounts or low-tier GCP).
*   **Difficulty:** Medium (requires some Google API setup).

---

## 3. Recommendation

For a **"Bloomberg Terminal"** look with **zero cost** and **low difficulty**, I recommend **Approach 3 (Possibility 1)**:
1.  **Backend:** FastAPI on GCP Cloud Run (Scale to zero = $0 cost when not used).
2.  **Frontend:** A React app with a Mono font (e.g., `JetBrains Mono`), dark background, and neon-green accents. 
3.  **Logic:** It calls your existing `Screener` logic.
4.  **Login:** Use a simple token-based login or Firebase Auth.

Would you like me to create a prototype of the **FastAPI** wrapper or the **Terminal CSS** frontend?
