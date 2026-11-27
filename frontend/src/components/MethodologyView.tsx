import React from 'react';
import { BookOpen, Calculator, ShieldCheck, TrendingUp } from 'lucide-react';

const FORMULAS = [
  {
    category: '1. Trailing Twelve Months (TTM) Normalization',
    color: 'text-terminal-cyan',
    items: [
      {
        name: 'TTM Flow Metric (Revenue, EBIT, CFO, CapEx)',
        formula: 'TTM = Current YTD + (Previous FY − Previous YTD)',
        notes: 'Standardizes 10-Q cumulative year-to-date numbers with prior 10-K audited full-year figures.',
      },
    ],
  },
  {
    category: '2. Joel Greenblatt — Magic Formula',
    color: 'text-terminal-green',
    items: [
      {
        name: 'Enterprise Value (EV)',
        formula: 'EV = Market Cap + Short-Term Debt + Long-Term Debt − Cash & Equivalents',
        notes: 'Represents total theoretical takeover cost of the business.',
      },
      {
        name: 'Earnings Yield (EY)',
        formula: 'EY = EBIT / EV',
        notes: 'Pre-tax operating yield relative to Enterprise Value (falls back to Market Cap if EV ≤ 0).',
      },
      {
        name: 'Tangible Capital Employed (TCE)',
        formula: 'TCE = Total Assets − Goodwill & Intangibles − Cash & Equivalents',
        notes: 'Net working capital plus net fixed operating assets.',
      },
      {
        name: 'Return on Capital (ROC)',
        formula: 'ROC = EBIT / TCE',
        notes: 'Operating efficiency on tangible capital deployed.',
      },
    ],
  },
  {
    category: '3. Bruce Greenwald — Reproduction Cost & EPV',
    color: 'text-terminal-amber',
    items: [
      {
        name: 'Asset Reproduction Value',
        formula: 'Reproduction Value = Total Assets − (Current Liabilities − Short-Term Debt)',
        notes: 'Subtracts non-interest-bearing operating liabilities (NIBCL) from total assets.',
      },
      {
        name: 'Earning Power Value (EPV)',
        formula: 'EPV = [EBIT × (1 − τ)] / WACC',
        notes: 'Steady-state zero-growth value with normalized tax rate τ = 25% and WACC = 10% (sensitivity 8%–12%).',
      },
      {
        name: 'Franchise / Moat Factor',
        formula: 'Moat Factor = EPV / Reproduction Value',
        notes: '> 1.0x indicates a durable competitive advantage.',
      },
    ],
  },
  {
    category: '4. FCFF Payback, ROIC & Total Return to Shareholders (TRS)',
    color: 'text-purple-400',
    items: [
      {
        name: 'Free Cash Flow to Firm (FCFF)',
        formula: 'FCFF = CFO − Interest Expense × (1 − Effective Tax Rate) − CapEx',
        notes: 'Effective Tax Rate = Income Tax / Pretax Income (clamped 0%–35%, fallback 25%).',
      },
      {
        name: 'FCFF Payback (TTM & 5Y Avg)',
        formula: 'MC / FCFF = Market Capitalization / FCFF (Years)',
        notes: 'Estimated years of unlevered free cash flow required to pay back current market cap.',
      },
      {
        name: 'ROIC (Invested Capital Definition)',
        formula: 'ROIC = [EBIT × (1 − Tax Rate)] / (Inventory + Receivables − Payables + Net Fixed Assets)',
        notes: 'After-tax operating return on net working capital + net PP&E across TTM, 3Y, 5Y, and 10Y.',
      },
      {
        name: 'Total Return to Shareholders (TRS)',
        formula: 'TRS (%) = [(P_end − P_start) / P_start] + [Σ Dividends / P_start]',
        notes: 'Decomposes shareholder return into price appreciation % plus cumulative dividend yield %.',
      },
    ],
  },
  {
    category: '5. Steady-State DCF & Quality / Solvency Checks',
    color: 'text-rose-400',
    items: [
      {
        name: 'Steady-State Gordon DCF',
        formula: 'Intrinsic Value = [FCF × (1 + g)] / (r − g)',
        notes: 'Default r = 9% discount rate, g = 2% perpetual growth (2D sensitivity grid 8%–10% × 1.5%–2.5%).',
      },
      {
        name: 'Non-Recurring CapEx Split',
        formula: 'Maintenance CapEx ≈ min(CapEx, D&A); Growth CapEx = max(0, CapEx − D&A)',
        notes: 'Flags CapEx / D&A ≥ 1.35x as expansion cycles alongside restructuring/impairment OpEx items.',
      },
      {
        name: 'Working Capital Divergence (Quality of Earnings)',
        formula: 'AR or Inventory Growth − Revenue Growth > 15%',
        notes: 'Flags potential channel stuffing or inventory obsolescence.',
      },
    ],
  },
];

export const MethodologyView: React.FC = () => {
  return (
    <div className="flex-1 overflow-y-auto bg-terminal-bg p-4 font-mono text-xs space-y-4">
      <div className="bg-terminal-card border border-terminal-border rounded p-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Calculator className="w-4 h-4 text-terminal-green" />
          <div>
            <div className="font-bold text-terminal-text text-sm">FINANCIAL METHODOLOGY &amp; FORMULA REFERENCE</div>
            <div className="text-[11px] text-terminal-muted">
              Every valuation model, ratio, and quality check computed from SEC EDGAR XBRL &amp; market data.
            </div>
          </div>
        </div>
        <span className="px-2 py-0.5 rounded bg-terminal-bg border border-terminal-border text-[10px] text-terminal-cyan">
          SOURCE: docs/METHODOLOGY.md
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {FORMULAS.map((sec) => (
          <div key={sec.category} className="bg-terminal-card border border-terminal-border rounded p-3 space-y-2.5">
            <div className={`font-bold border-b border-terminal-border pb-1.5 flex items-center gap-1.5 ${sec.color}`}>
              <BookOpen className="w-3.5 h-3.5" />
              <span>{sec.category}</span>
            </div>
            <div className="space-y-2">
              {sec.items.map((item) => (
                <div key={item.name} className="p-2 rounded bg-terminal-bg border border-terminal-border/50 space-y-1">
                  <div className="font-bold text-terminal-text text-[11.5px] flex items-center gap-1.5">
                    <TrendingUp className="w-3 h-3 text-terminal-muted" />
                    <span>{item.name}</span>
                  </div>
                  <div className="px-2 py-1 rounded bg-terminal-panel border border-terminal-border/60 text-terminal-green text-[11px] font-semibold">
                    {item.formula}
                  </div>
                  <div className="text-[10.5px] text-terminal-muted">{item.notes}</div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="p-3 rounded bg-terminal-card/70 border border-terminal-border text-[11px] text-terminal-muted flex items-center gap-2">
        <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
        <span>
          All fundamentals prioritize primary SEC XBRL filings via <code>edgartools</code>; market prices, shares float, and dividend history use <code>yfinance</code>.
        </span>
      </div>
    </div>
  );
};
