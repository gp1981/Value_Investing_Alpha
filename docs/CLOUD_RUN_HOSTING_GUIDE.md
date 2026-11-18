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
