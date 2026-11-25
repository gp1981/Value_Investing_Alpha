import React, { useEffect, useState } from 'react';
import { Users, ExternalLink, TrendingUp, ArrowUpRight, ArrowDownRight, Sparkles } from 'lucide-react';
import { SuperinvestorProfile, SuperinvestorPortfolioResponse } from '../types';

interface SuperinvestorsViewProps {
  onSelectTicker: (ticker: string) => void;
}

const formatMoney = (val: number) => {
  if (!val) return '$0';
  if (val >= 1e9) return `$${(val / 1e9).toFixed(2)}B`;
  if (val >= 1e6) return `$${(val / 1e6).toFixed(2)}M`;
  return `$${val.toLocaleString()}`;
};

export const SuperinvestorsView: React.FC<SuperinvestorsViewProps> = ({ onSelectTicker }) => {
  const [investors, setInvestors] = useState<SuperinvestorProfile[]>([]);
  const [selectedCik, setSelectedCik] = useState<string>('0001067983');
  const [portfolio, setPortfolio] = useState<SuperinvestorPortfolioResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState<string>('');

  useEffect(() => {
    fetch('/api/superinvestors/list')
      .then((r) => r.json())
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          setInvestors(data);
        }
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!selectedCik) return;
    setIsLoading(true);
    setError(null);
    fetch(`/api/superinvestors/${selectedCik}`)
      .then(async (res) => {
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || `Failed to load 13F portfolio (${res.status})`);
        }
        return res.json();
      })
      .then((data: SuperinvestorPortfolioResponse) => setPortfolio(data))
      .catch((err) => {
        setError(err.message);
        setPortfolio(null);
      })
      .finally(() => setIsLoading(false));
  }, [selectedCik]);

  const activeProfile = investors.find((i) => i.cik === selectedCik);
  const filteredHoldings = (portfolio?.holdings || []).filter((h) => {
    if (!searchTerm.trim()) return true;
    const q = searchTerm.toLowerCase();
    return (
      h.issuer.toLowerCase().includes(q) ||
      (h.ticker && h.ticker.toLowerCase().includes(q)) ||
      h.cusip.toLowerCase().includes(q)
    );
  });

  return (
    <div className="flex-1 flex flex-col lg:flex-row overflow-hidden bg-terminal-bg font-mono text-xs">
      {/* Left Sidebar: Curated Value Superinvestors */}
      <div className="w-full lg:w-72 border-b lg:border-b-0 lg:border-r border-terminal-border bg-terminal-panel overflow-y-auto shrink-0">
        <div className="p-2.5 border-b border-terminal-border bg-terminal-card flex items-center gap-2">
          <Users className="w-3.5 h-3.5 text-terminal-green" />
          <span className="font-bold text-terminal-text tracking-wider">VALUE SUPERINVESTORS (13F)</span>
        </div>
        <div className="divide-y divide-terminal-border/40">
          {investors.map((inv) => {
            const active = inv.cik === selectedCik;
            return (
              <button
                key={inv.cik}
                onClick={() => setSelectedCik(inv.cik)}
                className={`w-full text-left p-2.5 transition-colors ${
                  active
                    ? 'bg-terminal-card border-l-2 border-terminal-green text-terminal-text'
                    : 'hover:bg-terminal-card/50 text-terminal-muted'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className={`font-bold ${active ? 'text-terminal-green' : 'text-terminal-text'}`}>
                    {inv.manager}
                  </span>
                  <span className="text-[10px] text-terminal-muted">CIK {inv.cik.slice(-6)}</span>
                </div>
                <div className="text-[11px] truncate text-terminal-cyan/90">{inv.fund_name}</div>
                <div className="text-[10px] text-terminal-muted truncate mt-0.5">{inv.style}</div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Content: 13F Holdings Table */}
      <div className="flex-1 flex flex-col overflow-hidden p-3 space-y-3 overflow-y-auto">
        <div className="px-3 py-1.5 rounded bg-terminal-card/70 border border-terminal-border text-[10.5px] text-terminal-muted">
          <span className="text-terminal-cyan font-bold">13F TRACKER:</span> Inspect latest quarterly US equity holdings &amp; QoQ changes of renowned value managers. Select a manager on the left; click any row with a ticker to open its full terminal analysis.
        </div>
        {activeProfile?.note && (
          <div className="px-3 py-1.5 rounded bg-amber-950/30 border border-amber-700/40 text-amber-300 text-[11px]">
            <strong>Note:</strong> {activeProfile.note}
          </div>
        )}

        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-24 text-terminal-muted space-y-2">
            <div className="animate-spin w-6 h-6 border-2 border-terminal-green border-t-transparent rounded-full" />
            <span>FETCHING LIVE SEC FORM 13F-HR HOLDINGS...</span>
          </div>
        ) : error ? (
          <div className="p-4 rounded bg-red-950/30 border border-red-700/50 text-terminal-red">
            {error}
          </div>
        ) : portfolio ? (
          <>
            {/* Summary Banner */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 bg-terminal-card p-3 rounded border border-terminal-border">
              <div>
                <div className="text-[10px] text-terminal-muted">MANAGER // FUND</div>
                <div className="font-bold text-terminal-green truncate">{portfolio.manager}</div>
                <div className="text-[10px] text-terminal-text truncate">{portfolio.fund_name}</div>
              </div>
              <div>
                <div className="text-[10px] text-terminal-muted">TOTAL 13F EQUITY VALUE</div>
                <div className="text-sm font-bold text-terminal-text tabular-numbers">
                  {formatMoney(portfolio.total_value_usd)}
                </div>
                <div className="text-[10px] text-terminal-muted">{portfolio.holdings_count} positions</div>
              </div>
              <div>
                <div className="text-[10px] text-terminal-muted">REPORT PERIOD // FILED</div>
                <div className="font-bold text-terminal-cyan">{portfolio.report_period || 'Latest'}</div>
                <div className="text-[10px] text-terminal-muted">Filed {portfolio.filing_date}</div>
              </div>
              <div className="flex flex-col justify-between items-start sm:items-end">
                {portfolio.sec_url && (
                  <a
                    href={portfolio.sec_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 text-[10px] text-terminal-cyan hover:underline"
                  >
                    <span>OFFICIAL SEC 13F-HR</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                )}
                <input
                  type="text"
                  placeholder="Filter issuer or ticker..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="mt-1 bg-terminal-bg border border-terminal-border rounded px-2 py-0.5 text-[11px] text-terminal-text w-full sm:w-44 focus:outline-none focus:border-terminal-green"
                />
              </div>
            </div>

            {/* Holdings Table */}
            <div className="border border-terminal-border rounded bg-terminal-card overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-[11px] tabular-numbers border-collapse">
                  <thead>
                    <tr className="bg-terminal-bg border-b border-terminal-border text-terminal-muted">
                      <th className="py-1.5 px-2.5 text-left">#</th>
                      <th className="py-1.5 px-2.5 text-left">TICKER</th>
                      <th className="py-1.5 px-2.5 text-left">ISSUER</th>
                      <th className="py-1.5 px-2.5 text-right">WEIGHT %</th>
                      <th className="py-1.5 px-2.5 text-right">MARKET VALUE</th>
                      <th className="py-1.5 px-2.5 text-right">SHARES</th>
                      <th className="py-1.5 px-2.5 text-right">QoQ ACTIVITY</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-terminal-border/30">
                    {filteredHoldings.map((h, idx) => (
                      <tr
                        key={`${h.cusip}-${idx}`}
                        onClick={() => h.ticker && onSelectTicker(h.ticker)}
                        className={`hover:bg-terminal-bg/70 transition-colors ${
                          h.ticker ? 'cursor-pointer' : ''
                        }`}
                      >
                        <td className="py-1 px-2.5 text-terminal-muted">{idx + 1}</td>
                        <td className="py-1 px-2.5 font-bold text-terminal-green">
                          {h.ticker || '—'}
                        </td>
                        <td className="py-1 px-2.5 text-terminal-text max-w-[260px] truncate">{h.issuer}</td>
                        <td className="py-1 px-2.5 text-right font-bold text-terminal-cyan">{h.weight_pct.toFixed(2)}%</td>
                        <td className="py-1 px-2.5 text-right text-terminal-text">{formatMoney(h.value_usd)}</td>
                        <td className="py-1 px-2.5 text-right text-terminal-muted">{h.shares.toLocaleString()}</td>
                        <td className="py-1 px-2.5 text-right">
                          {h.activity === 'NEW' && (
                            <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-600/50 text-[10px] font-bold">
                              <Sparkles className="w-2.5 h-2.5" /> NEW
                            </span>
                          )}
                          {h.activity === 'ADDED' && (
                            <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-emerald-950/60 text-emerald-400 text-[10px] font-bold">
                              <ArrowUpRight className="w-2.5 h-2.5" /> +{h.share_change_pct}%
                            </span>
                          )}
                          {h.activity === 'REDUCED' && (
                            <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-rose-950/60 text-rose-400 text-[10px] font-bold">
                              <ArrowDownRight className="w-2.5 h-2.5" /> {h.share_change_pct}%
                            </span>
                          )}
                          {(h.activity === 'UNCHANGED' || h.activity === 'HELD') && (
                            <span className="text-terminal-muted text-[10px]">{h.activity}</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
};
