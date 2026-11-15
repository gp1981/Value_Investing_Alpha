import React from 'react';
import { Search, SlidersHorizontal, ArrowUpDown } from 'lucide-react';

interface ToolbarProps {
  search: string;
  onSearchChange: (val: string) => void;
  minCap: number;
  onMinCapChange: (cap: number) => void;
  sortBy: string;
  onSortByChange: (sort: string) => void;
  sortOrder: 'asc' | 'desc';
  onToggleSortOrder: () => void;
  selectedSector: string;
  onSectorChange: (sector: string) => void;
}

const SECTORS = ['ALL', 'Technology', 'Healthcare', 'Consumer', 'Industrial', 'Semiconductors'];

export const Toolbar: React.FC<ToolbarProps> = ({
  search,
  onSearchChange,
  minCap,
  onMinCapChange,
  sortBy,
  onSortByChange,
  sortOrder,
  onToggleSortOrder,
  selectedSector,
  onSectorChange,
}) => {
  return (
    <div className="bg-terminal-card border-b border-terminal-border px-3 py-1.5 flex flex-wrap items-center justify-between gap-2 text-xs">
      {/* Search Input */}
      <div className="flex items-center gap-2 flex-1 min-w-[200px] max-w-[320px]">
        <div className="relative w-full">
          <Search className="w-3.5 h-3.5 text-terminal-muted absolute left-2 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="FILTER TICKER OR COMPANY..."
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full bg-terminal-bg border border-terminal-border rounded pl-7 pr-2 py-1 text-xs text-terminal-text placeholder-terminal-muted focus:outline-none focus:border-terminal-cyan transition-colors"
          />
        </div>
      </div>

      {/* Sector Quick Filters */}
      <div className="hidden lg:flex items-center gap-1">
        <span className="text-[10px] text-terminal-muted mr-1">SECTOR:</span>
        {SECTORS.map((sec) => (
          <button
            key={sec}
            onClick={() => onSectorChange(sec)}
            className={`px-1.5 py-0.5 rounded text-[10px] uppercase transition-colors border ${
              selectedSector === sec
                ? 'bg-terminal-cyan/15 text-terminal-cyan border-terminal-cyan/40 font-semibold'
                : 'bg-terminal-panel text-terminal-muted border-terminal-border hover:text-terminal-text'
            }`}
          >
            {sec}
          </button>
        ))}
      </div>

      {/* Controls: Cap & Sorting */}
      <div className="flex items-center gap-2">
        {/* Min Market Cap Select */}
        <div className="flex items-center gap-1 bg-terminal-bg px-2 py-0.5 rounded border border-terminal-border text-[11px]">
          <span className="text-terminal-muted">MIN CAP:</span>
          <select
            value={minCap}
            onChange={(e) => onMinCapChange(Number(e.target.value))}
            className="bg-transparent text-terminal-text focus:outline-none cursor-pointer"
          >
            <option value={0} className="bg-terminal-panel">ANY</option>
            <option value={50000000} className="bg-terminal-panel">$50M (Micro)</option>
            <option value={500000000} className="bg-terminal-panel">$500M (Small)</option>
            <option value={2000000000} className="bg-terminal-panel">$2B (Mid)</option>
            <option value={10000000000} className="bg-terminal-panel">$10B (Large)</option>
          </select>
        </div>

        {/* Sort Select */}
        <div className="flex items-center gap-1 bg-terminal-bg px-2 py-0.5 rounded border border-terminal-border text-[11px]">
          <SlidersHorizontal className="w-3 h-3 text-terminal-muted" />
          <span className="text-terminal-muted">SORT:</span>
          <select
            value={sortBy}
            onChange={(e) => onSortByChange(e.target.value)}
            className="bg-transparent text-terminal-text focus:outline-none cursor-pointer"
          >
            <option value="magic_formula_rank" className="bg-terminal-panel">Magic Formula Rank</option>
            <option value="earnings_yield" className="bg-terminal-panel">Earnings Yield (EY)</option>
            <option value="return_on_capital" className="bg-terminal-panel">Return on Capital (ROC)</option>
            <option value="epv_margin_of_safety" className="bg-terminal-panel">EPV Margin of Safety</option>
            <option value="market_cap" className="bg-terminal-panel">Market Cap</option>
          </select>

          <button
            onClick={onToggleSortOrder}
            className="text-terminal-cyan hover:text-terminal-green pl-1 ml-1 border-l border-terminal-border transition-colors uppercase font-bold"
            title="Toggle sort direction"
          >
            {sortOrder}
          </button>
        </div>
      </div>
    </div>
  );
};
