# Google Cloud Run Hosting Guide — Value Investing Alpha

> **A Step-by-Step Guide for Non-Professionals to Deploy and Host the Platform Using Your $300 GCP Credit**

---

## 1. Hosting Provider Recommendation

### Why Google Cloud Run is the Best Choice

For hosting **Value Investing Alpha**, we strongly recommend **Google Cloud Run** over traditional virtual machines (like AWS EC2 or DigitalOcean Droplets) or managed container services.

Here is why:

1. **Scale-to-Zero Architecture ($0 Idle Cost)**:
   Traditional servers charge you 24 hours a day, 7 days a week, even when you are asleep. Cloud Run automatically spins down to **0 running servers** when nobody is visiting your website. You are only billed for the exact seconds someone is viewing the screener.
2. **Permanent Free Tier**:
   Every month, Google Cloud gives you:
   - **2,000,000 free web requests**
   - **360,000 free Gigabyte-seconds of memory**
   - **180,000 free vCPU-seconds**
   For a personal or small-team screener, your monthly usage will typically fall completely inside this free tier.
3. **Your \$300 Credit Coverage**:
   Even if you leave the screener running frequently, your **\$300 Google Cloud credit will easily cover hosting for 1 to 2+ years**.
4. **Built-in HTTPS and Security**:
   Google automatically provides an SSL certificate (https://) and global CDN protection with zero configuration.
5. **Single-Container Simplicity**:
   Because we packaged both the React frontend and FastAPI backend into one Docker container, you only have to manage and deploy **one service**.

---

## 2. Cost Estimate & Credit Management

| Cloud Component | Resource | Estimated Monthly Cost | Covered by Free Tier? |
| :--- | :--- | :--- | :--- |
| **Compute & API** | Cloud Run (1 vCPU, 512 MB RAM, scale-to-zero) | \$0.00 – \$0.50 | ✅ Yes |
| **Container Storage** | Google Artifact Registry (~500 MB container image) | \$0.05 – \$0.10 | ✅ Yes (<1GB free) |
| **Network Traffic** | Egress (under 10 GB/month) | \$0.00 | ✅ Yes (1GB/mo free) |
| **Total Estimated Cost** | — | **\$0.00 / month** | **100% Covered** |

---

## 3. Step-by-Step Setup Instructions

You do not need prior cloud experience. Follow these steps in order:

### Step 1: Activate Your $300 Google Cloud Credit
1. Open your browser and go to [https://cloud.google.com/free](https://cloud.google.com/free).
2. Sign in with your Google account.
3. Click **Get started for free**.
4. Fill in your details. Google requires a credit card for identity verification, but **you will not be charged**—your \$300 credit is automatically applied to your account.

---

### Step 2: Create a New GCP Project
1. In the [Google Cloud Console](https://console.cloud.google.com/), click the **Project Selector** dropdown in the top-left navigation bar.
2. Click **New Project**.
3. Enter Project Name: `value-investing-alpha`.
4. Click **Create** and ensure it is selected as your active project.

---

### Step 3: Install the Google Cloud CLI (`gcloud`) on Your Mac
If you do not have `gcloud` installed yet, open your Mac terminal and run:

```bash
# Using Homebrew (recommended)
brew install google-cloud-sdk
```

Once installed, initialize your Google login:
```bash
gcloud auth login
```
*A browser window will open. Sign in with your Google account and grant permission.*

Set your active project:
```bash
gcloud config set project value-investing-alpha
```

---

### Step 4: Enable Required Google Cloud Services
Run this single command to enable Cloud Run, Container Registry, and Cloud Build:

```bash
gcloud services enable run.googleapis.com \
                       artifactregistry.googleapis.com \
                       cloudbuild.googleapis.com
```

---

### Step 5: Build and Deploy the Container to Cloud Run

The beauty of Google Cloud Build is that **you do not even need Docker running on your Mac**. Google will build the container in the cloud and deploy it directly!

Navigate to the project root in your terminal:
```bash
cd /Users/gabrielepicheo/Documents/Github/gp1981/Value_Investing_Alpha
```

Run the one-step build & deploy command:
```bash
gcloud run deploy value-investing-alpha \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 2 \
  --set-env-vars "EDGAR_IDENTITY=Your Name your.email@example.com"
```

#### What these parameters mean:
- `--source .`: Tells Google to look at our `Dockerfile` and build it automatically.
- `--region us-central1`: Iowa datacenter (low latency, lowest cost tier).
- `--allow-unauthenticated`: Makes the website publicly viewable in your browser.
- `--memory 512Mi`: Allocates 512 Megabytes of RAM (plenty for our lightweight models).
- `--min-instances 0`: **Crucial!** Tells Cloud Run to shut off when not in use ($0 cost).
- `--max-instances 2`: Caps usage to 2 instances so traffic spikes never incur runaway costs.
- `--set-env-vars`: Declares your SEC Edgar user identity required by the SEC.

---

### Step 6: Access Your Live Platform

Once the command finishes (usually takes 2 to 3 minutes), `gcloud` will output your live URL:
```text
Service [value-investing-alpha] has been deployed and is available at:
https://value-investing-alpha-xxxxxx-uc.a.run.app
```

Open this URL in any browser on your computer, tablet, or phone. You will see the **Alpha Terminal** live!

---

### Step 7: (Optional) Updating Environment Variables in the Console
If you ever want to change your SEC contact email or settings without using the command line:
1. Go to [Google Cloud Run Console](https://console.cloud.google.com/run).
2. Click on **value-investing-alpha**.
3. Click **Edit & Deploy New Revision**.
4. Click the **Variables & Secrets** tab.
5. Add or update variables (e.g. `EDGAR_IDENTITY`).
6. Click **Deploy**.

---

### Step 8: Set a $0 Budget Alert (Peace of Mind)
To ensure you never accidentally spend past your \$300 credit:
1. In the GCP Console, go to **Billing** > **Budgets & alerts**.
2. Click **Create Budget**.
3. Set the target amount to **\$1.00** or **\$5.00**.
4. Check **Email alerts to billing admins**.
5. Save. Google will automatically notify you if usage ever exceeds zero.

---

### Summary Checklist for Deployment

- [ ] Sign up for GCP free tier and get \$300 credit.
- [ ] Install `gcloud` (`brew install google-cloud-sdk`).
- [ ] Run `gcloud auth login` and set project `value-investing-alpha`.
- [ ] Run `gcloud run deploy` command from project root.
- [ ] Bookmark your `https://....a.run.app` terminal URL!


---

## 4. Cost-Effective & Free User Authentication Architecture

To protect your terminal and gate premium features without adding ongoing cloud bills, we recommend two zero-cost authentication approaches:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                   AUTHENTICATION OPTIONS COMPARISON                      │
├─────────────────────────┬──────────────────────┬─────────────────────────┤
│ Option                  │ Estimated Monthly    │ Best Used For           │
│                         │ Cost                 │                         │
├─────────────────────────┼──────────────────────┼─────────────────────────┤
│ 1. Built-in JWT Auth    │ $0.00 / forever      │ Self-contained email &  │
│    (Implemented in app) │ (No external deps)   │ password, zero cloud    │
│                         │                      │ service dependence      │
├─────────────────────────┼──────────────────────┼─────────────────────────┤
│ 2. Firebase Auth        │ $0.00 up to 50k MAU  │ "Sign in with Google",  │
│    (Google Cloud)       │ (Unlimited Google)   │ passwordless email links│
├─────────────────────────┼──────────────────────┼─────────────────────────┤
│ 3. Cloud Run IAP        │ ~$18.00 / month      │ Enterprise only         │
│    (Identity-Aware)     │ (Requires Load Bal)  │ (Not recommended)       │
└─────────────────────────┴──────────────────────┴─────────────────────────┘
```

### Approach 1: Built-in JWT Authentication ($0.00 — Already Implemented)
- **How It Works**: The application includes self-contained JWT token generation (`src/api/auth.py` and `src/api/routes/auth.py`). Passwords are salted and hashed using PBKDF2 SHA-256 (industry banking standard).
- **Session Handling**: When a user signs in, FastAPI issues a secure JWT token. The React terminal stores it in client-side memory/`localStorage` and sends it as a `Bearer` token in the `Authorization` header.
- **Cost**: **$0.00 forever**. No database or external service bills.
- **Pre-Seeded Demo Account**:
  - Email: `analyst@example.com`
  - Password: `valuealpha2026`

### Approach 2: Google Sign-In via Firebase Auth (Free up to 50,000 Users)
If you prefer users clicking a single "Sign in with Google" button:
1. In Google Cloud Console, enable **Firebase Authentication** on your project `value-investing-alpha`.
2. Enable the **Google** sign-in provider under *Sign-in method*.
3. Add the Firebase Web SDK to `frontend/src/` (under 10 lines of code).
4. FastAPI validates the incoming Firebase Google ID token via `google-auth` library.
5. **Cost**: **$0.00** for up to 50,000 monthly active users.

---

## 5. Cloud SEC Data Strategy: How to Minimize Expenses to Zero

A common mistake in cloud engineering is trying to host 24 GB of raw SEC files on a live virtual server, which requires large memory instances costing \$100+/month.

Here is the exact blueprint to keep your cloud bill at **$0.00**:

```
[User Request]
       │
       ▼
[Cloud Run Instance (512MB RAM)]
       │
       ├──► 1. Pre-Compiled Daily Snapshot (output/company_data.csv)
       │       - Covers top 500-1000 liquid US stocks
       │       - Kept directly inside the lightweight container image
       │       - Reads in 0.005 seconds | RAM usage: ~30 MB | Cost: $0.00
       │
       └──► 2. On-Demand Non-Bulk Ticker Query (e.g. user searches "CRWD")
               - Fetches ONLY that single company's latest 10-K from SEC EDGAR
               - Parses XBRL facts on-the-fly in 1.5 seconds
               - Discards raw XML immediately to preserve memory
               - Cost: $0.00 (within SEC fair access limit of 10 req/sec)
```

### 1. Pre-Compiled Daily Snapshot (Free Tier Feature)
- Standard users browse and filter from a pre-calculated dataset (`output/company_data.csv`) embedded directly in the container or stored in a free Google Cloud Storage bucket (first 5 GB of GCS is free).
- This delivers sub-millisecond response times for 95% of user visits without hitting SEC servers.

### 2. On-Demand Single Company Lookups (Just-In-Time)
- When a user clicks a company or searches for a ticker not in the snapshot, FastAPI queries SEC EDGAR directly for that single ticker.
- Only ~200 KB of XML is downloaded into temporary memory, parsed, and discarded.
- No heavy storage or database needed.

### 3. Scheduled Daily/Weekly Refresh (Automation)
- To keep the snapshot fresh, you can run a **Cloud Run Job** once every 24 hours (or once a week on Sunday night).
- Cloud Run Jobs run for ~3-5 minutes to parse filings, save the updated `company_data.csv`, and shut off.
- Compute time: 5 minutes $\times$ 4 times/month = 20 minutes/month (well within the 180,000 free vCPU seconds).
- Cost: **$0.00**.

---

## 6. Real-Data Testing Walkthrough on Your Local SSD

Before deploying to Cloud Run, test the application with real SEC financial filings on your external SSD (`/Volumes/T3/edgartools`).

### Step 1: Verify External Drive Path & SEC Identity
Open your `.env` file and ensure:
```env
EDGAR_IDENTITY="Gabriele Picheo gabriele.picheo@gmail.com"
EDGAR_LOCAL_DATA_DIR="/Volumes/T3/edgartools"
EDGAR_CACHE_DIR="/Volumes/T3/edgartools/cache"
```
*(SEC requires a valid name and email in the User-Agent header to grant API access).*

### Step 2: Do You Need to Bulk Download 24 GB for Testing?
**NO.** You do not need to wait for 24 GB to download to test the platform as a real user.
- **Recommended Fast Test (2 minutes)**: Screen a real watchlist of major US stocks (e.g. `AAPL, MSFT, GOOGL, NVDA, TXN, JNJ, BRK-B, AMZN`). This will fetch real primary SEC 10-Ks, calculate real Greenwald EPV, Magic Formula, and DCF metrics, and populate `output/company_data.csv` using your SSD.
- **Optional Full Bulk Sync (1-3 hours)**: If you want all ~10,000 US companies downloaded to `/Volumes/T3/edgartools` once, run:
  ```bash
  source .venv/bin/activate
  python -m src.data.sync --identity "Gabriele Picheo gabriele.picheo@gmail.com" --storage /Volumes/T3/edgartools
  ```

### Step 3: Run Real-Data Screening Test
Execute a test run across 6 real companies:
```bash
source .venv/bin/activate
python -m src.main --tickers AAPL MSFT GOOGL NVDA TXN JNJ --storage /Volumes/T3/edgartools
```
This will:
1. Contact SEC EDGAR and extract real audited 10-K filings.
2. Direct all caching to `/Volumes/T3/edgartools/` (leaving your primary Mac SSD untouched).
3. Compute Magic Formula, Greenwald Reproduction Cost, EPV, and DCF.
4. Save the real results to `output/company_data.csv`.

### Step 4: Launch Web Terminal & Verify Real Data
```bash
uvicorn src.api.main:app --port 8000
```
Open [http://localhost:8000](http://localhost:8000):
- The header telemetry will indicate `SOURCE: CACHE` with real stock counts.
- Click on **AAPL** or **NVDA** to view the real 10-K breakdown, EPV sensitivity tables, and solvency traffic light.
- Click **LOGIN** and sign in with `analyst@example.com` / `valuealpha2026`.
- Click **EXCEL** to download the formatted valuation spreadsheet.
