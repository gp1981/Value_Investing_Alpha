# Financial Methodology & Variable Reference

This document provides a comprehensive mathematical, financial, and architectural specification for all valuation models, safety indicators, growth metrics, and screening variables used in the **Value Investing Screener**.

---

## Table of Contents
1. [Trailing Twelve Months (TTM) Normalization](#1-trailing-twelve-months-ttm-normalization)
2. [Magic Formula Model (Joel Greenblatt)](#2-magic-formula-model-joel-greenblatt)
3. [Bruce Greenwald Framework (Asset Reproduction & EPV)](#3-bruce-greenwald-framework-asset-reproduction--epv)
4. [Discounted Cash Flow (DCF) Model](#4-discounted-cash-flow-dcf-model)
5. [Cash Flow & Free Cash Flow Yield](#5-cash-flow--free-cash-flow-yield)
6. [Safety & Liquidity Signals (SafetyModel)](#6-safety--liquidity-signals-safetymodel)
7. [Statistical Outlier Signals (Revenue Z-Score)](#7-statistical-outlier-signals-revenue-z-score)
8. [Multi-Decade Equity CAGR Reconstruction](#8-multi-decade-equity-cagr-reconstruction)
9. [Working Capital & Quality of Earnings Anomaly Detection](#9-working-capital--quality-of-earnings-anomaly-detection)
10. [Market Multiples & Capital Structure Ratios](#10-market-multiples--capital-structure-ratios)

---

## 1. Trailing Twelve Months (TTM) Normalization

Financial statements for flow items (Revenue, EBIT, Net Income, Cash Flows) in quarterly 10-Q filings are cumulative year-to-date (YTD). To guarantee comparability between companies filing 10-K (12 months) and 10-Q (3, 6, or 9 months), all flow metrics are converted to a rolling 12-month period.

### Formula
$$\text{TTM} = \text{Current YTD} + (\text{Previous FY} - \text{Previous YTD})$$

### Components
*   **Current YTD**: Cumulative flow from the beginning of the current fiscal year through the latest reported quarter.
*   **Previous FY**: Full 12-month audited flow from the previous fiscal year (10-K).
*   **Previous YTD**: Cumulative flow from the beginning of the prior fiscal year through the matching prior quarter.

### Intuition
Subtracting `Previous YTD` from `Previous FY` isolates the second half / remaining quarters of the prior year. Adding those to `Current YTD` forms an exact 12-month window reflecting the latest operations.

---

## 2. Magic Formula Model (Joel Greenblatt)

The Magic Formula ranks non-financial companies by combining two primary valuation metrics: **Earnings Yield (EY)** and **Return on Capital (ROC)**.

### 2.1 Earnings Yield (EY)
Measures the operating return relative to total enterprise purchase cost.

$$\text{Earnings Yield} = \frac{\text{EBIT}}{\text{Enterprise Value (EV)}}$$

*   **EBIT (Operating Income)**: Standardized operating income derived from SEC filings (`OperatingIncomeLoss`, `PretaxIncomeLoss`, or revenue minus operating costs).
*   **Enterprise Value (EV)**:
    $$\text{EV} = \text{Market Capitalization} + \text{Total Debt} - \text{Cash \& Cash Equivalents}$$
    *   $\text{Market Capitalization} = \text{Share Price} \times \text{Shares Outstanding}$
    *   $\text{Total Debt} = \text{Short-Term Debt} + \text{Long-Term Debt}$
    *   *Constraint Handling*: If $\text{EBIT} \le 0$, $\text{EY} = 0.0$. If $\text{EV} \le 0$, the model falls back to Market Capitalization as denominator: $\text{EY} = \frac{\text{EBIT}}{\text{Market Cap}}$.

### 2.2 Return on Capital (ROC)
Measures operating efficiency on tangible operating assets deployed.

$$\text{Return on Capital} = \frac{\text{EBIT}}{\text{Tangible Capital Employed (TCE)}}$$

*   **Tangible Capital Employed (TCE)**:
    $$\text{TCE} = \text{Total Assets} - \text{Goodwill \& Intangible Assets} - \text{Cash \& Cash Equivalents}$$
    *   *Constraint Handling*: If $\text{TCE} \le 0$, it indicates extreme asset-light leverage or negative net tangible assets (e.g., companies funded entirely by trade credit); the model assigns a high ROC cap ($1,000\%$) to reflect infinite capital efficiency without divide-by-zero errors.

### 2.3 Industry-Aware Excess Cash Refinement
Standard implementations treat 100% of cash as excess. The screener optionally refines this by estimating non-operating cash:
1. Calculate the median $\frac{\text{Cash}}{\text{Revenue}}$ ratio across all peers sharing the same 4-digit SIC code:
   $$\text{Ratio}_{\text{SIC}} = \text{Median}\left(\frac{\text{Cash}_i}{\text{Revenue}_i}\right)$$
2. Operating Cash Requirement:
   $$\text{Operating Cash} = \text{Ratio}_{\text{SIC}} \times \text{Revenue}$$
3. Excess Non-Operating Cash:
   $$\text{Excess Cash} = \max\left(0, \text{Total Cash} - \text{Operating Cash}\right)$$

### 2.4 Magic Formula Ranking
1. Rank all companies descending by `EY (%)` $\rightarrow \text{Rank}_{\text{EY}}$ (Rank 1 = Highest Earnings Yield).
2. Rank all companies descending by `ROC (%)` $\rightarrow \text{Rank}_{\text{ROC}}$ (Rank 1 = Highest Return on Capital).
3. Combine ranks:
   $$\text{Magic Rank} = \text{Rank}_{\text{EY}} + \text{Rank}_{\text{ROC}}$$
4. Sort by $\text{Magic Rank}$ ascending to produce sequential `Magic Formula Rank` (1, 2, 3...).

---

## 3. Bruce Greenwald Framework (Asset Reproduction & EPV)

Bruce Greenwald evaluates businesses along a three-tier hierarchy: **Asset Value**, **Earning Power Value (EPV)**, and **Franchise Value**.

### 3.1 Asset Reproduction Value
Estimates the capital an entrant would need to duplicate the operating assets of the incumbent firm:

$$\text{Reproduction Value} = \text{Total Assets} - \text{Non-Interest-Bearing Current Liabilities (NIBCL)}$$

Where:
$$\text{NIBCL} = \text{Current Liabilities} - \text{Short-Term Debt}$$

*Interpretation*: Non-interest-bearing operating liabilities (like Accounts Payable and accrued liabilities) are spontaneous financing provided by suppliers and operations, reducing the net capital an entrant must commit.

### 3.2 Earning Power Value (EPV)
Measures the steady-state value of current earnings power assuming **zero future growth** and 100% distribution of earnings:

$$\text{EPV} = \frac{\text{Adjusted Operating Earnings} \times (1 - \tau)}{\text{Cost of Capital (WACC)}}$$

Where:
*   $\text{Adjusted Operating Earnings} = \text{EBIT}$ (operating earnings under current capacity).
*   $\tau = \text{Normalized Tax Rate}$ (standardized at $25\%$ or $0.25$).
*   $\text{WACC} = \text{Cost of Capital / Discount Rate}$ (derived from the 10-year historical return of the S&P 500 with dividends reinvested).

### 3.3 EPV / Market Cap Ratio (`EPV/MC`)
$$\frac{\text{EPV}}{\text{MC}} = \frac{\text{EPV}}{\text{Market Capitalization}}$$
*   **$\frac{\text{EPV}}{\text{MC}} > 1.0$**: The company trades below the present value of its steady-state earnings, indicating a margin of safety without needing to pay for growth.
*   **$\text{EPV} > \text{Reproduction Value}$**: Indicates competitive advantage (Franchise / Moat) where current assets generate returns exceeding reproduction cost.

---

## 4. Discounted Cash Flow (DCF) Model

Evaluates steady-state intrinsic valuation using a capitalized single-stage Gordon growth model applied to normalized free cash flows.

### Formula
$$\text{Intrinsic Value} = \frac{\text{FCF} \times (1 + g)}{r - g}$$

### Variables
*   **FCF (Free Cash Flow Proxy)**:
    $$\text{FCF} = \text{Net Income} + \text{Depreciation \& Amortization} - \text{Capital Expenditures (CapEx)}$$
    *(If CapEx or D&A are missing in older filings, Net Income is utilized as a conservative floor).*
*   $r$: **Discount Rate** (10-year historical S&P 500 total return, typically ~9.5%–11.5%).
*   $g$: **Perpetual Growth Rate** (conservative steady-state rate set to $2.0\%$ or $0.02$).

### DCF / Market Cap Ratio (`DCF/MC`)
$$\frac{\text{DCF}}{\text{MC}} = \frac{\text{Intrinsic Value}}{\text{Market Capitalization}}$$
*   $\frac{\text{DCF}}{\text{MC}} > 1.0$: Company is undervalued relative to steady-state discounted cash flows.
*   If $\text{FCF} \le 0$ or $r \le g$, intrinsic value is zero.

---

## 5. Cash Flow & Free Cash Flow Yield

Measures actual cash generative capacity compared to accounting net income.

### 5.1 Operating Cash Flow (OCF)
Cash provided by operating activities as reported in the Statement of Cash Flows (`OperatingCashFlowLoss` or standardized `CashFlowFromOperations`).

### 5.2 Free Cash Flow (FCF)
The actual discretionary cash generated by the business after investing in capital assets needed to maintain or expand productive capacity:

$$\text{FCF} = \text{Operating Cash Flow} - \text{Capital Expenditures (CapEx)}$$

### 5.3 Free Cash Flow Yield (`fcf_yield (%)`)
The cash return earned by an investor on the current equity market capitalization:

$$\text{FCF Yield (\%)} = \left( \frac{\text{Free Cash Flow}_{\text{TTM}}}{\text{Market Capitalization}} \right) \times 100$$

*Interpretation*: High FCF Yield (>7–10%) indicates cash generative strength and strong debt service/distribution capability.

---

## 6. Safety & Liquidity Signals (SafetyModel)

Evaluates short-term balance sheet fragility and default risk using a synthetic Traffic Light composite.

### 6.1 Liquidity & Solvency Ratios
1.  **Quick Ratio**:
    $$\text{Quick Ratio} = \frac{\text{Current Assets} - \text{Inventory}}{\text{Current Liabilities}}$$
2.  **Debt to Equity (D/E)**:
    $$\text{D/E} = \frac{\text{Short-Term Debt} + \text{Long-Term Debt}}{\text{Shareholders' Equity}}$$
    *(If Equity $\le 0$, D/E is penalized with 999.0).*
3.  **Debt to Assets (D/A)**:
    $$\text{D/A} = \frac{\text{Total Debt}}{\text{Total Assets}}$$

### 6.2 Traffic Light Signal (`Output`)
The composite traffic light classifies solvency into three distinct risk tiers:

| Signal | Color | Quick Ratio | Debt / Equity | Debt / Assets | Interpretation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **GREEN** | Safe | $\ge 2.0$ | $\le 0.33$ | $\le 0.20$ | Fortress balance sheet: pristine liquidity, negligible leverage. |
| **YELLOW**| Moderate | $\ge 1.0$ | $\le 1.00$ | $\le 0.35$ | Adequate working capital; manageable leverage. |
| **RED** | Fragile | Any other combination | Deficient liquidity or excessive debt. Heightened solvency risk. |

---

## 7. Statistical Outlier Signals (Revenue Z-Score)

Detects whether the latest reported quarter's top-line revenue is an abnormal statistical outlier relative to the company's recent operational trend.

### 7.1 Historical Dataset
An 8-quarter chronological revenue series $R = \{R_1, R_2, \dots, R_8\}$ extracted directly from SEC quarterly XBRL filings or local facts.

### 7.2 Formulation
1. **Sample Mean**:
   $$\mu = \frac{1}{N} \sum_{i=1}^{N} R_i$$
2. **Sample Standard Deviation**:
   $$\sigma = \sqrt{\frac{1}{N} \sum_{i=1}^{N} (R_i - \mu)^2}$$
3. **Z-Score of Latest Quarter**:
   $$Z_{\text{rev}} = \frac{R_{\text{latest}} - \mu}{\sigma}$$

### 7.3 Revenue Z-Score Classification (`Revenue ZScore`)
*   **High** ($Z_{\text{rev}} > +2.0$): Revenue is over 2 standard deviations above the 8-quarter mean (unusual seasonal surge, acquisition spike, or one-off contract).
*   **Low** ($Z_{\text{rev}} < -2.0$): Revenue is over 2 standard deviations below the mean (macro shock, lost contract, or operational interruption).
*   **Normal** ($-2.0 \le Z_{\text{rev}} \le +2.0$): Revenue aligns within expected operational variance.
*   **N/A**: Fewer than 2 positive historical quarters available.

---

## 8. Multi-Decade Equity CAGR Reconstruction

Accounting book value of equity understates true long-term shareholder value creation because dividends, share buybacks, and debt-funded distributions are subtracted from balance sheet retained earnings.

The **Equity Analysis Model** reconstructs what shareholders' equity would have grown to over a multi-decade span (up to 20 years) by adding back distributions and adjusting for debt.

### 8.1 Time Horizon & Baseline Variables
*   $t_0$: Date of oldest available annual 10-K filing.
*   $t_{\text{last}}$: Date of most recent 10-K filing.
*   $\Delta t = \text{Years Analyzed} = \frac{t_{\text{last}} - t_0}{365.25}$.
*   $E_0 = \text{Initial Equity}$: Shareholders' equity at $t_0$.
*   $E_t = \text{Last Equity}$: Shareholders' equity at $t_{\text{last}}$.
*   $D_0, D_t$: Total debt at $t_0$ and $t_{\text{last}}$, with $\Delta \text{Debt} = D_t - D_0$.

### 8.2 Cumulative Cash Distributions
*   $\text{Cum. Dividends Paid} = \sum_{k=1}^{n} |\text{Dividends}_k|$
*   $\text{Cum. Net Repurchases} = \sum_{k=1}^{n} |\text{Repurchases}_k| - \sum_{k=1}^{n} \text{Issuances}_k$
*   $\text{Total Distributions} = \text{Cum. Dividends Paid} + \text{Cum. Net Repurchases}$
*   $\text{Cum. Net Income} = \sum_{k=1}^{n} \text{Net Income}_k$

### 8.3 The Three Full Equity CAGR Variants

#### Variant 1: CAGR Full Equity (`CAGR Full Equity (%)`)
Reconstructs total shareholder equity creation by adding back all capital returned via dividends and net share buybacks:

$$E_{\text{full}} = E_t + \text{Cum. Dividends Paid} + \text{Cum. Net Repurchases}$$

$$\text{CAGR Full Equity} = \left( \frac{E_{\text{full}}}{E_0} \right)^{\frac{1}{\Delta t}} - 1$$

*Rationale*: Represents the compound growth of shareholder capital if all distributed cash had been retained inside the corporate structure.

#### Variant 2: CAGR Full Equity with Debt Adjustment (`CAGR Full Equity w/ Debt (%)`)
Penalizes financial engineering where distributions or buybacks were financed by taking on debt rather than through organic operating cash generation:

$$\text{Debt Offset} = \min\left( \max(0, \Delta \text{Debt}),\; \text{Total Distributions} \right)$$

$$E_{\text{debt\_adj}} = E_{\text{full}} - \text{Debt Offset}$$

$$\text{CAGR Full Equity w/ Debt} = \left( \frac{E_{\text{debt\_adj}}}{E_0} \right)^{\frac{1}{\Delta t}} - 1$$

*Rationale*: If a company borrowed $\$10\text{B}$ to execute buybacks, that $\$10\text{B}$ does not represent organic equity growth; this adjustment strips out leveraged distributions.

#### Variant 3: CAGR Full Equity Net Income (`CAGR Full Equity NI (%)`)
Measures equity growth based purely on cumulative accounting net income retained over the period:

$$E_{\text{NI}} = E_0 + \text{Cum. Net Income}$$

$$\text{CAGR Full Equity NI} = \left( \frac{E_{\text{NI}}}{E_0} \right)^{\frac{1}{\Delta t}} - 1$$

*Rationale*: Serves as a baseline benchmark of cumulative profitability independent of balance sheet items, goodwill impairments, and financing activities.

---

## 9. Working Capital & Quality of Earnings Anomaly Detection

Identifies potential accounting distortions, aggressive revenue recognition, or operational inventory buildup by comparing working capital growth rates against top-line revenue growth.

### 9.1 Background & Intuition
In a healthy business, Accounts Receivable ($\text{AR}$) and Inventory ($\text{Inv}$) typically grow in tandem with Revenue ($\text{Rev}$).
*   **Accounts Receivable growing significantly faster than Revenue**: May indicate channel stuffing, unearned revenue recognition, relaxed customer credit standards, or deteriorating collections.
*   **Inventory growing significantly faster than Revenue**: May signal slowing product demand, obsolete stock buildup, or future write-downs.

### 9.2 Formulation
For consecutive fiscal years or comparable TTM periods ($t$ vs $t-1$):

1.  **Revenue Growth**:
    $$\Delta \text{Rev} = \frac{\text{Revenue}_t - \text{Revenue}_{t-1}}{\text{Revenue}_{t-1}}$$
2.  **Accounts Receivable Growth**:
    $$\Delta \text{AR} = \frac{\text{AR}_t - \text{AR}_{t-1}}{\text{AR}_{t-1}}$$
3.  **Inventory Growth**:
    $$\Delta \text{Inv} = \frac{\text{Inventory}_t - \text{Inventory}_{t-1}}{\text{Inventory}_{t-1}}$$

### 9.3 Divergence Differentials
*   **AR Divergence**:
    $$\text{Div}_{\text{AR}} = \Delta \text{AR} - \Delta \text{Rev}$$
*   **Inventory Divergence**:
    $$\text{Div}_{\text{Inv}} = \Delta \text{Inv} - \Delta \text{Rev}$$

### 9.4 Classification Logic (`WC Anomaly Signal`)
*   **WARNING**:
    *   $\text{Div}_{\text{AR}} > +15\%$ (with $\Delta \text{AR} > 0$), OR
    *   $\text{Div}_{\text{Inv}} > +15\%$ (with $\Delta \text{Inv} > 0$ for inventory-carrying businesses).
*   **ELEVATED**:
    *   $+10\% < \text{Div}_{\text{AR}} \le +15\%$, OR
    *   $+10\% < \text{Div}_{\text{Inv}} \le +15\%$.
*   **NORMAL**: Working capital growth aligns within $\pm 10\%$ of top-line revenue growth.
*   **N/A**: Prior-year comparative data unavailable or non-positive baseline.

---

## 10. Market Multiples & Capital Structure Ratios

Standard valuation and capital structure ratios computed for secondary screening:

| Metric | Code Key | Formula | Purpose |
| :--- | :--- | :--- | :--- |
| **Price to Earnings** | `pe_ratio` | $\frac{\text{Price}}{\text{EPS}_{\text{TTM}}} = \frac{\text{Price}}{\text{Net Income} / \text{Shares}}$ | Market price relative to per-share accounting earnings. |
| **Price to Book** | `pb_ratio` | $\frac{\text{Price}}{\text{BVPS}_{\text{TTM}}} = \frac{\text{Price}}{\text{Shareholders' Equity} / \text{Shares}}$ | Market price relative to net asset book value per share. |
| **Equity over Debt** | `e_over_d` | $\frac{\text{Shareholders' Equity}}{\text{Short-Term Debt} + \text{Long-Term Debt}}$ | Capital cushion ratio measuring equity buffer protecting debt. |
| **Market Cap ($M)** | `market_cap_musd`| $\frac{\text{Market Capitalization}}{10^6}$ | Scaled market capitalization in millions of USD. |
| **Free Cash Flow Yield** | `fcf_yield (%)` | $\left( \frac{\text{Free Cash Flow}_{\text{TTM}}}{\text{Market Capitalization}} \right) \times 100$ | Discretionary cash earnings yield on equity. |
