import React, { useEffect, useState } from 'react';
import { X, Award, Layers, TrendingUp, ShieldCheck, Grid3X3, FileText, ExternalLink, Filter } from 'lucide-react';
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
  const [filingFilter, setFilingFilter] = useState<'ALL' | '10-K' | '10-Q' | '8-K'>('ALL');

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

  // Helper calculations for EPV and DCF Sensitivity Matrices
  const shares = data?.shares_outstanding || 1;
  const price = data?.price || 1;
  const ebit = data?.magic_formula.ebit || 0;
  const normalizedTaxRate = data?.greenwald.tax_rate || 0.25;
  const normalizedEarnings = ebit * (1 - normalizedTaxRate);

  // EPV Sensitivity: WACC rates
  const epvWaccSteps = [0.08, 0.09, 0.10, 0.11, 0.12];

  // DCF Sensitivity Matrix: discount rate vs growth rate
  const dcfDiscountRates = [0.08, 0.09, 0.10];
  const dcfGrowthRates = [0.015, 0.02, 0.025];
  const fcf = (data?.financial_statement?.net_income || 0) +
    (data?.financial_statement?.depreciation_amortization || 0) -
    (data?.financial_statement?.capex || 0);

  return (
    <div className="fixed inset-y-0 right-0 w-full sm:w-[580px] bg-terminal-panel border-l border-terminal-border z-30 shadow-2xl flex flex-col font-mono text-xs select-none">
      {/* Drawer Header */}
      <div className="border-b border-terminal-border p-3 flex items-center justify-between bg-terminal-card">
        <div className="flex items-center gap-2">
          <span className="text-base font-bold text-terminal-green tracking-wider">{ticker}</span>
          <span className="text-terminal-muted truncate max-w-[300px]">
            {data?.company_name || (isLoading ? 'FETCHING SEC FILINGS & FACTS...' : 'VALUATION BREAKDOWN')}
          </span>
        </div>
        <button
          onClick={onClose}
          className="text-terminal-muted hover:text-terminal-text p-1 rounded hover:bg-terminal-border transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Top Animated Loading Pulse Bar */}
      {isLoading && (
        <div className="w-full h-0.5 bg-terminal-border overflow-hidden">
          <div className="w-full h-full bg-gradient-to-r from-terminal-green via-terminal-cyan to-terminal-green animate-pulse" />
        </div>
      )}

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
                <div className="text-[10px] text-terminal-muted">MARKET PRICE</div>
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
              </div>

              {/* EPV Sensitivity Sub-Table */}
              <div className="mt-2 pt-2 border-t border-terminal-border/40">
                <span className="text-[10px] text-terminal-muted block mb-1">EPV HURDLE SENSITIVITY TABLE:</span>
                <div className="grid grid-cols-5 gap-1 text-[10px] tabular-numbers text-center bg-terminal-bg p-1.5 rounded border border-terminal-border">
                  {epvWaccSteps.map((wacc) => {
                    const stepEpvPerShare = (normalizedEarnings / wacc) / shares;
                    const stepMos = (stepEpvPerShare - price) / stepEpvPerShare;
                    return (
                      <div key={wacc} className="border-r border-terminal-border/30 last:border-0">
                        <div className="text-terminal-muted">{(wacc * 100).toFixed(0)}% WACC</div>
                        <div className="text-terminal-text font-bold">${stepEpvPerShare.toFixed(1)}</div>
                        <div className={stepMos > 0 ? 'text-terminal-green font-semibold' : 'text-terminal-red'}>
                          {(stepMos * 100).toFixed(0)}%
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* 3. DCF Steady-State Valuation & Sensitivity Matrix */}
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
              </div>

              {/* 2D DCF Sensitivity Matrix */}
              <div className="mt-2 pt-2 border-t border-terminal-border/40">
                <div className="flex items-center gap-1 text-[10px] text-terminal-muted mb-1">
                  <Grid3X3 className="w-3 h-3 text-terminal-amber" />
                  <span>DCF SENSITIVITY MATRIX (DISCOUNT RATE vs PERPETUAL GROWTH):</span>
                </div>
                <table className="w-full text-[10px] tabular-numbers border-collapse text-center">
                  <thead>
                    <tr className="border-b border-terminal-border text-terminal-muted">
                      <th className="py-0.5 px-1 text-left">r \ g</th>
                      {dcfGrowthRates.map((g) => (
                        <th key={g} className="py-0.5 px-1">{(g * 100).toFixed(1)}%</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {dcfDiscountRates.map((r) => (
                      <tr key={r} className="border-b border-terminal-border/30 hover:bg-terminal-bg">
                        <td className="py-0.5 px-1 text-left text-terminal-muted font-bold">{(r * 100).toFixed(0)}%</td>
                        {dcfGrowthRates.map((g) => {
                          let valPerShare = 0;
                          if (r > g && fcf > 0) {
                            const valTotal = (fcf * (1 + g)) / (r - g);
                            valPerShare = valTotal / shares;
                          }
                          const isUnder = valPerShare > price;
                          return (
                            <td
                              key={g}
                              className={`py-0.5 px-1 font-semibold ${
                                isUnder ? 'text-terminal-green bg-emerald-950/20' : 'text-terminal-text'
                              }`}
                            >
                              ${valPerShare > 0 ? valPerShare.toFixed(1) : '—'}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
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

            {/* 5. SEC Regulatory Filings Explorer */}
            <div className="border border-terminal-border bg-terminal-card rounded p-3 space-y-2">
              <div className="flex items-center justify-between border-b border-terminal-border pb-1.5">
                <div className="flex items-center gap-1.5 text-terminal-cyan font-semibold">
                  <FileText className="w-3.5 h-3.5 text-terminal-cyan" />
                  <span>
                    SEC REGULATORY FILINGS (
                    {(data.filings || []).filter(f => filingFilter === 'ALL' || f.form === filingFilter).length}
                    )
                  </span>
                </div>
                {/* Filter Chips */}
                <div className="flex items-center gap-1 text-[10px]">
                  {(['ALL', '10-K', '10-Q', '8-K'] as const).map((filter) => (
                    <button
                      key={filter}
                      onClick={() => setFilingFilter(filter)}
                      className={`px-1.5 py-0.5 rounded transition-colors ${
                        filingFilter === filter
                          ? 'bg-terminal-cyan/20 text-terminal-cyan border border-terminal-cyan/50 font-bold'
                          : 'text-terminal-muted hover:text-terminal-text hover:bg-terminal-border'
                      }`}
                    >
                      {filter}
                    </button>
                  ))}
                </div>
              </div>

              {(!data.filings || data.filings.filter(f => filingFilter === 'ALL' || f.form === filingFilter).length === 0) ? (
                <div className="py-4 text-center text-terminal-muted text-[10px]">
                  No {filingFilter} filings found in local SEC repository.
                </div>
              ) : (
                <div className="max-h-56 overflow-y-auto divide-y divide-terminal-border/30 text-[10px]">
                  {data.filings
                    .filter(f => filingFilter === 'ALL' || f.form === filingFilter)
                    .map((filing) => {
                      const is10K = filing.form === '10-K';
                      const is10Q = filing.form === '10-Q';
                      const badgeClass = is10K
                        ? 'border-amber-500/50 text-amber-400 bg-amber-950/40'
                        : is10Q
                        ? 'border-cyan-500/50 text-cyan-400 bg-cyan-950/40'
                        : 'border-purple-500/50 text-purple-400 bg-purple-950/40';

                      return (
                        <div key={filing.accession_number} className="py-2 px-1 hover:bg-terminal-bg/50 transition-colors space-y-1">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-1.5">
                              <span className={`px-1.5 py-0.5 rounded font-bold border text-[9px] ${badgeClass}`}>
                                {filing.form}
                              </span>
                              <span className="text-terminal-text font-semibold">{filing.filing_date}</span>
                              {filing.report_date && (
                                <span className="text-terminal-muted text-[9px]">
                                  (Period: {filing.report_date})
                                </span>
                              )}
                            </div>
                            <div className="flex items-center gap-2">
                              {filing.interactive_url && (
                                <a
                                  href={filing.interactive_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-terminal-cyan/15 text-terminal-cyan hover:bg-terminal-cyan/25 border border-terminal-cyan/40 transition-colors font-medium text-[9px]"
                                  title="Open Official SEC Interactive Data Viewer"
                                >
                                  <span>XBRL VIEWER</span>
                                  <ExternalLink className="w-2.5 h-2.5" />
                                </a>
                              )}
                              {filing.url && (
                                <a
                                  href={filing.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-terminal-border/50 text-terminal-muted hover:text-terminal-text hover:bg-terminal-border transition-colors text-[9px]"
                                  title="Open SEC EDGAR Filing Directory"
                                >
                                  <span>SEC INDEX</span>
                                  <ExternalLink className="w-2.5 h-2.5" />
                                </a>
                              )}
                            </div>
                          </div>
                          <div className="flex items-center justify-between text-terminal-muted text-[9px] font-mono">
                            <span className="truncate max-w-[320px]">{filing.description || filing.form}</span>
                            <span className="text-[8px] text-terminal-muted/60">{filing.accession_number}</span>
                          </div>
                        </div>
                      );
                    })}
                </div>
              )}
            </div>

            {/* 6. Raw XBRL Financial Statement Items */}
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
