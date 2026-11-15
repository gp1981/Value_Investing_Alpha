import React, { useEffect, useState } from 'react';
import { X, ExternalLink, ShieldCheck, TrendingUp, Award, Layers } from 'lucide-react';
import { CompanyDetailResponse } from '../types';

interface CompanyDrawerProps {
  ticker: string | null;
  onClose: () => void;
}

const formatCurrencyCompact = (val?: number | null) => {
  if (val === null || val === undefined || isNaN(val)) return '—';
  if (Math.abs(val) >= 1e12) return `$${(val / 1e12).toFixed(2)}T`;
  if (Math.abs(val) >= 1e9) return `$${(val / 1e9).toFixed(2)}B`;
  if (Math.abs(val) >= 1e6) return `$${(val / 1e6).toFixed(2)}M`;
  return `$${val.toLocaleString()}`;
};

const formatPercent = (val?: number | null) => {
  if (val === null || val === undefined || isNaN(val)) return '—';
  return `${(val * 100).toFixed(2)}%`;
};

export const CompanyDrawer: React.FC<CompanyDrawerProps> = ({ ticker, onClose }) => {
  const [data, setData] = useState<CompanyDetailResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!ticker) {
      setData(null);
      return;
    }

    const fetchDetails = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const res = await fetch(`/api/company/${ticker}`);
        if (!res.ok) {
          throw new Error(`Failed to load details for ${ticker}`);
        }
        const json = await res.json();
        setData(json);
      } catch (err: any) {
        setError(err.message || 'Error fetching company valuation data');
      } finally {
        setIsLoading(false);
      }
    };

    fetchDetails();
  }, [ticker]);

  if (!ticker) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-full sm:w-[540px] bg-terminal-panel border-l border-terminal-border z-30 shadow-2xl flex flex-col font-mono text-xs">
      {/* Drawer Header */}
      <div className="border-b border-terminal-border p-3 flex items-center justify-between bg-terminal-card">
        <div className="flex items-center gap-2">
          <span className="text-base font-bold text-terminal-green tracking-wider">{ticker}</span>
          <span className="text-terminal-muted truncate max-w-[280px]">
            {data?.company_name || 'LOADING...'}
          </span>
        </div>
        <button
          onClick={onClose}
          className="text-terminal-muted hover:text-terminal-text p-1 rounded hover:bg-terminal-border transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Drawer Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {isLoading && (
          <div className="flex flex-col items-center justify-center py-20 text-terminal-muted">
            <div className="animate-spin w-6 h-6 border-2 border-terminal-cyan border-t-transparent rounded-full mb-2" />
            <span>EXTRACTING 10-K / 10-Q XBRL FACTS...</span>
          </div>
        )}

        {error && (
          <div className="p-3 bg-red-950/40 border border-red-800/50 rounded text-terminal-red">
            {error}
          </div>
        )}

        {data && !isLoading && (
          <>
            {/* Quick Summary Pill Bar */}
            <div className="grid grid-cols-3 gap-2 bg-terminal-bg p-2.5 rounded border border-terminal-border text-center">
              <div>
                <div className="text-[10px] text-terminal-muted">PRICE</div>
                <div className="text-sm font-bold text-terminal-text tabular-numbers">${data.price.toFixed(2)}</div>
              </div>
              <div>
                <div className="text-[10px] text-terminal-muted">MARKET CAP</div>
                <div className="text-sm font-bold text-terminal-text tabular-numbers">{formatCurrencyCompact(data.market_cap)}</div>
              </div>
              <div>
                <div className="text-[10px] text-terminal-muted">SOLVENCY</div>
                <div className="mt-0.5">
                  <span
                    className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                      data.safety.traffic_light === 'GREEN'
                        ? 'bg-emerald-950 text-emerald-400 border border-emerald-600/50'
                        : data.safety.traffic_light === 'YELLOW'
                        ? 'bg-amber-950 text-amber-400 border border-amber-600/50'
                        : 'bg-rose-950 text-rose-400 border border-rose-600/50'
                    }`}
                  >
                    {data.safety.traffic_light}
                  </span>
                </div>
              </div>
            </div>

            {/* 1. Magic Formula Breakdown */}
            <div className="border border-terminal-border bg-terminal-card rounded p-3 space-y-2">
              <div className="flex items-center gap-1.5 text-terminal-green font-semibold border-b border-terminal-border pb-1">
                <Award className="w-3.5 h-3.5 text-terminal-green" />
                <span>JOEL GREENBLATT // MAGIC FORMULA</span>
              </div>
              <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-[11px] tabular-numbers pt-1">
                <div className="flex justify-between border-b border-terminal-border/30 pb-0.5">
                  <span className="text-terminal-muted">Operating EBIT:</span>
                  <span className="text-terminal-text font-medium">{formatCurrencyCompact(data.magic_formula.ebit)}</span>
                </div>
                <div className="flex justify-between border-b border-terminal-border/30 pb-0.5">
                  <span className="text-terminal-muted">Enterprise Value:</span>
                  <span className="text-terminal-text font-medium">{formatCurrencyCompact(data.magic_formula.enterprise_value)}</span>
                </div>
                <div className="flex justify-between border-b border-terminal-border/30 pb-0.5">
                  <span className="text-terminal-muted">Earnings Yield (EY):</span>
                  <span className="text-terminal-green font-bold">{formatPercent(data.magic_formula.earnings_yield)}</span>
                </div>
                <div className="flex justify-between border-b border-terminal-border/30 pb-0.5">
                  <span className="text-terminal-muted">Return on Capital:</span>
                  <span className="text-terminal-cyan font-bold">{formatPercent(data.magic_formula.return_on_capital)}</span>
                </div>
                <div className="flex justify-between col-span-2 pt-0.5">
                  <span className="text-terminal-muted">Tangible Capital Employed:</span>
                  <span className="text-terminal-text">{formatCurrencyCompact(data.magic_formula.tangible_capital_employed)}</span>
                </div>
              </div>
            </div>

            {/* 2. Bruce Greenwald EPV vs Reproduction Cost */}
            <div className="border border-terminal-border bg-terminal-card rounded p-3 space-y-2">
              <div className="flex items-center gap-1.5 text-terminal-cyan font-semibold border-b border-terminal-border pb-1">
                <Layers className="w-3.5 h-3.5 text-terminal-cyan" />
                <span>BRUCE GREENWALD // EPV & REPRODUCTION</span>
              </div>
              <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-[11px] tabular-numbers pt-1">
                <div className="flex justify-between border-b border-terminal-border/30 pb-0.5">
                  <span className="text-terminal-muted">Reproduction Cost / Sh:</span>
                  <span className="text-terminal-text font-medium">${data.greenwald.reproduction_value_per_share.toFixed(2)}</span>
                </div>
                <div className="flex justify-between border-b border-terminal-border/30 pb-0.5">
                  <span className="text-terminal-muted">Earning Power Value / Sh:</span>
                  <span className="text-terminal-cyan font-bold">${data.greenwald.epv_per_share.toFixed(2)}</span>
                </div>
                <div className="flex justify-between border-b border-terminal-border/30 pb-0.5">
                  <span className="text-terminal-muted">Franchise Moat Ratio:</span>
                  <span className={`font-semibold ${data.greenwald.franchise_factor > 1 ? 'text-terminal-green' : 'text-terminal-amber'}`}>
                    {data.greenwald.franchise_factor.toFixed(2)}x {data.greenwald.franchise_factor > 1 ? '(MOAT)' : ''}
                  </span>
                </div>
                <div className="flex justify-between border-b border-terminal-border/30 pb-0.5">
                  <span className="text-terminal-muted">EPV Margin of Safety:</span>
                  <span className={`font-bold ${data.greenwald.margin_of_safety > 0 ? 'text-terminal-green' : 'text-terminal-red'}`}>
                    {formatPercent(data.greenwald.margin_of_safety)}
                  </span>
                </div>
                <div className="flex justify-between col-span-2 pt-0.5">
                  <span className="text-terminal-muted">Cost of Capital (WACC):</span>
                  <span className="text-terminal-text">{formatPercent(data.greenwald.wacc)}</span>
                </div>
              </div>
            </div>

            {/* 3. DCF Steady-State Valuation */}
            <div className="border border-terminal-border bg-terminal-card rounded p-3 space-y-2">
              <div className="flex items-center gap-1.5 text-terminal-amber font-semibold border-b border-terminal-border pb-1">
                <TrendingUp className="w-3.5 h-3.5 text-terminal-amber" />
                <span>STEADY-STATE DISCOUNTED CASH FLOW (DCF)</span>
              </div>
              <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-[11px] tabular-numbers pt-1">
                <div className="flex justify-between border-b border-terminal-border/30 pb-0.5">
                  <span className="text-terminal-muted">DCF Intrinsic / Share:</span>
                  <span className="text-terminal-text font-bold">${data.dcf.intrinsic_value_per_share.toFixed(2)}</span>
                </div>
                <div className="flex justify-between border-b border-terminal-border/30 pb-0.5">
                  <span className="text-terminal-muted">DCF Margin of Safety:</span>
                  <span className={`font-semibold ${data.dcf.margin_of_safety > 0 ? 'text-terminal-green' : 'text-terminal-red'}`}>
                    {formatPercent(data.dcf.margin_of_safety)}
                  </span>
                </div>
                <div className="flex justify-between col-span-2 pt-0.5">
                  <span className="text-terminal-muted">Discount / Perpetual Growth:</span>
                  <span className="text-terminal-text">{formatPercent(data.dcf.discount_rate)} / {formatPercent(data.dcf.growth_rate)}</span>
                </div>
              </div>
            </div>

            {/* 4. Solvency & Safety Metrics */}
            <div className="border border-terminal-border bg-terminal-card rounded p-3 space-y-2">
              <div className="flex items-center gap-1.5 text-terminal-text font-semibold border-b border-terminal-border pb-1">
                <ShieldCheck className="w-3.5 h-3.5 text-terminal-cyan" />
                <span>SOLVENCY & WORKING CAPITAL AUDIT</span>
              </div>
              <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-[11px] tabular-numbers pt-1">
                <div className="flex justify-between border-b border-terminal-border/30 pb-0.5">
                  <span className="text-terminal-muted">Quick Ratio:</span>
                  <span className="text-terminal-text">{data.safety.quick_ratio.toFixed(2)}</span>
                </div>
                <div className="flex justify-between border-b border-terminal-border/30 pb-0.5">
                  <span className="text-terminal-muted">Debt / Equity:</span>
                  <span className="text-terminal-text">{data.safety.debt_to_equity.toFixed(2)}</span>
                </div>
                <div className="flex justify-between border-b border-terminal-border/30 pb-0.5">
                  <span className="text-terminal-muted">Debt / Assets:</span>
                  <span className="text-terminal-text">{data.safety.debt_to_assets.toFixed(2)}</span>
                </div>
                <div className="flex justify-between border-b border-terminal-border/30 pb-0.5">
                  <span className="text-terminal-muted">WC Divergence:</span>
                  <span className="text-terminal-text">{data.safety.wc_anomaly_signal}</span>
                </div>
              </div>
            </div>

            {/* 5. Raw XBRL Financial Statement Items */}
            <div className="border border-terminal-border bg-terminal-card rounded p-3 space-y-2">
              <span className="text-[10px] text-terminal-muted uppercase tracking-wider block border-b border-terminal-border pb-1">
                SEC XBRL FILING DATA POINTS (TTM)
              </span>
              <div className="max-h-48 overflow-y-auto divide-y divide-terminal-border/30 text-[10px] tabular-numbers">
                {Object.entries(data.financial_statement).map(([key, value]) => {
                  if (typeof value === 'object' && value !== null) return null;
                  return (
                    <div key={key} className="flex justify-between py-0.5 hover:bg-terminal-bg px-1">
                      <span className="text-terminal-muted font-mono">{key}</span>
                      <span className="text-terminal-text font-mono">
                        {typeof value === 'number' ? formatCurrencyCompact(value) : String(value ?? '—')}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};
