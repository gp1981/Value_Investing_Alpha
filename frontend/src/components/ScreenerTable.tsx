import React from 'react';
import { StockItem } from '../types';
import { ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';

interface ScreenerTableProps {
  items: StockItem[];
  selectedTicker: string | null;
  onSelectTicker: (ticker: string) => void;
  isLoading: boolean;
}

const formatNumber = (val?: number | null, decimals = 2) => {
  if (val === null || val === undefined || isNaN(val)) return '—';
  return val.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
};

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

export const ScreenerTable: React.FC<ScreenerTableProps> = ({
  items,
  selectedTicker,
  onSelectTicker,
  isLoading,
}) => {
  if (isLoading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-12 text-terminal-muted">
        <div className="animate-spin w-8 h-8 border-2 border-terminal-cyan border-t-transparent rounded-full mb-3" />
        <span className="text-xs tracking-wider">RETRIEVING XBRL FILINGS & MARKET DATA...</span>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-12 text-terminal-muted">
        <Minus className="w-8 h-8 mb-2 opacity-50" />
        <span className="text-xs">NO COMPANIES MATCH CURRENT SCREEN CRITERIA</span>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-auto bg-terminal-bg">
      <table className="w-full border-collapse text-left select-text">
        <thead className="sticky top-0 bg-terminal-panel z-10 border-b border-terminal-border text-[10px] text-terminal-muted uppercase tracking-wider">
          <tr>
            <th className="py-1 px-2 border-r border-terminal-border w-10 text-center">RK</th>
            <th className="py-1 px-2 border-r border-terminal-border w-16">SYM</th>
            <th className="py-1 px-2 border-r border-terminal-border min-w-[150px]">COMPANY</th>
            <th className="py-1 px-2 border-r border-terminal-border hidden sm:table-cell w-28">SECTOR</th>
            <th className="py-1 px-2 border-r border-terminal-border text-right w-20">PRICE</th>
            <th className="py-1 px-2 border-r border-terminal-border text-right w-24">MKT CAP</th>
            <th className="py-1 px-2 border-r border-terminal-border text-right w-20 text-amber-300" title="Market Cap / TTM FCFF (Years to Payback)">MC/FCFF</th>
            <th className="py-1 px-2 border-r border-terminal-border text-right hidden md:table-cell w-20 text-amber-300" title="Market Cap / 5Y Avg FCFF (Years to Payback)">MC/FCFF 5Y</th>
            <th className="py-1 px-2 border-r border-terminal-border text-right hidden md:table-cell w-24">EV</th>
            <th className="py-1 px-2 border-r border-terminal-border text-right hidden lg:table-cell w-24">EBIT</th>
            <th className="py-1 px-2 border-r border-terminal-border text-right w-20 text-terminal-green">EY (EBIT/EV)</th>
            <th className="py-1 px-2 border-r border-terminal-border text-right w-20 text-terminal-cyan">ROC</th>
            <th className="py-1 px-2 border-r border-terminal-border text-right hidden xl:table-cell w-20">REP/SH</th>
            <th className="py-1 px-2 border-r border-terminal-border text-right hidden xl:table-cell w-20">EPV/SH</th>
            <th className="py-1 px-2 border-r border-terminal-border text-right w-20">EPV MOS</th>
            <th className="py-1 px-2 text-center w-14">SOLV</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-terminal-border/50 text-[11px] font-mono">
          {items.map((row) => {
            const isSelected = selectedTicker === row.ticker;
            const mos = row.epv_margin_of_safety ?? 0;
            const isUndervalued = mos > 0;

            return (
              <tr
                key={row.ticker}
                onClick={() => onSelectTicker(row.ticker)}
                className={`dense-tr cursor-pointer tabular-numbers ${
                  isSelected ? 'bg-terminal-borderLight/30 text-white font-medium' : 'text-terminal-text'
                }`}
              >
                {/* Rank */}
                <td className="py-1 px-2 border-r border-terminal-border/50 text-center text-terminal-muted text-[10px]">
                  {row.rank}
                </td>

                {/* Ticker */}
                <td className="py-1 px-2 border-r border-terminal-border/50 font-bold text-terminal-cyan tracking-wider">
                  {row.ticker}
                </td>

                {/* Company Name */}
                <td className="py-1 px-2 border-r border-terminal-border/50 truncate max-w-[200px]" title={row.company_name}>
                  {row.company_name}
                </td>

                {/* Sector */}
                <td className="py-1 px-2 border-r border-terminal-border/50 text-terminal-muted hidden sm:table-cell truncate max-w-[120px]">
                  {row.sector}
                </td>

                {/* Price */}
                <td className="py-1 px-2 border-r border-terminal-border/50 text-right">
                  ${formatNumber(row.price)}
                </td>

                {/* Market Cap */}
                <td className="py-1 px-2 border-r border-terminal-border/50 text-right text-terminal-muted">
                  {formatCurrencyCompact(row.market_cap)}
                </td>

                {/* Market Cap / FCFF TTM Payback */}
                <td className="py-1 px-2 border-r border-terminal-border/50 text-right text-amber-300 font-semibold">
                  {row.mc_to_fcff_ttm != null ? `${row.mc_to_fcff_ttm.toFixed(1)}x` : '—'}
                </td>

                {/* Market Cap / FCFF 5Y Avg Payback */}
                <td className="py-1 px-2 border-r border-terminal-border/50 text-right text-amber-300/80 hidden md:table-cell">
                  {row.mc_to_fcff_5y_avg != null ? `${row.mc_to_fcff_5y_avg.toFixed(1)}x` : '—'}
                </td>

                {/* EV */}
                <td className="py-1 px-2 border-r border-terminal-border/50 text-right text-terminal-muted hidden md:table-cell">
                  {formatCurrencyCompact(row.enterprise_value)}
                </td>

                {/* EBIT */}
                <td className="py-1 px-2 border-r border-terminal-border/50 text-right hidden lg:table-cell">
                  {formatCurrencyCompact(row.ebit)}
                </td>

                {/* Earnings Yield */}
                <td className="py-1 px-2 border-r border-terminal-border/50 text-right text-terminal-green font-semibold">
                  {formatPercent(row.earnings_yield)}
                </td>

                {/* Return on Capital */}
                <td className="py-1 px-2 border-r border-terminal-border/50 text-right text-terminal-cyan font-semibold">
                  {formatPercent(row.return_on_capital)}
                </td>

                {/* Reproduction Value / Share */}
                <td className="py-1 px-2 border-r border-terminal-border/50 text-right text-terminal-muted hidden xl:table-cell">
                  ${formatNumber(row.reproduction_value_per_share)}
                </td>

                {/* EPV / Share */}
                <td className="py-1 px-2 border-r border-terminal-border/50 text-right text-terminal-muted hidden xl:table-cell">
                  ${formatNumber(row.epv_per_share)}
                </td>

                {/* Margin of Safety */}
                <td
                  className={`py-1 px-2 border-r border-terminal-border/50 text-right font-medium flex items-center justify-end gap-0.5 ${
                    isUndervalued ? 'text-terminal-green' : 'text-terminal-red/80'
                  }`}
                >
                  {isUndervalued ? (
                    <ArrowUpRight className="w-3 h-3 text-terminal-green inline" />
                  ) : (
                    <ArrowDownRight className="w-3 h-3 text-terminal-red inline" />
                  )}
                  <span>{formatPercent(mos)}</span>
                </td>

                {/* Traffic Light */}
                <td className="py-1 px-2 text-center">
                  <span
                    className={`inline-block px-1.5 py-0.2 rounded text-[9px] font-bold ${
                      row.traffic_light === 'GREEN'
                        ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-600/40'
                        : row.traffic_light === 'YELLOW'
                        ? 'bg-amber-950/80 text-amber-400 border border-amber-600/40'
                        : 'bg-rose-950/80 text-rose-400 border border-rose-600/40'
                    }`}
                  >
                    {row.traffic_light}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
