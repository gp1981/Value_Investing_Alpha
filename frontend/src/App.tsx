import React, { useState, useEffect, useMemo } from 'react';
import { Header } from './components/Header';
import { Toolbar } from './components/Toolbar';
import { ScreenerTable } from './components/ScreenerTable';
import { CompanyDrawer } from './components/CompanyDrawer';
import { StockItem, ScreenerResponse } from './types';

export const App: React.FC = () => {
  const [items, setItems] = useState<StockItem[]>([]);
  const [source, setSource] = useState<string>('INIT');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);

  // Filters & Sorting state
  const [search, setSearch] = useState<string>('');
  const [minCap, setMinCap] = useState<number>(50000000);
  const [sortBy, setSortBy] = useState<string>('magic_formula_rank');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [selectedSector, setSelectedSector] = useState<string>('ALL');

  const fetchResults = async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams({
        limit: '100',
        sort_by: sortBy,
        sort_order: sortOrder,
        min_market_cap: minCap.toString(),
      });

      if (selectedSector !== 'ALL') {
        params.append('sector', selectedSector);
      }

      const res = await fetch(`/api/screener/results?${params.toString()}`);
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      const data: ScreenerResponse = await res.json();
      setItems(data.items);
      setSource(data.source);
    } catch (err) {
      console.warn('API error, falling back to local preview:', err);
      // Fallback preview data so the user always has a responsive interface
      setItems([
        {
          rank: 1,
          ticker: 'AAPL',
          company_name: 'Apple Inc.',
          sector: 'Technology',
          sic_code: 3571,
          price: 225.50,
          market_cap: 3450000000000,
          enterprise_value: 3520000000000,
          ebit: 123000000000,
          earnings_yield: 0.0349,
          return_on_capital: 0.582,
          magic_formula_rank: 1,
          reproduction_value_per_share: 22.88,
          epv_per_share: 60.29,
          epv_margin_of_safety: -0.73,
          traffic_light: 'GREEN',
          wc_anomaly: 'NORMAL',
        },
        {
          rank: 2,
          ticker: 'MSFT',
          company_name: 'Microsoft Corporation',
          sector: 'Technology',
          sic_code: 7372,
          price: 420.25,
          market_cap: 3120000000000,
          enterprise_value: 3150000000000,
          ebit: 109000000000,
          earnings_yield: 0.0346,
          return_on_capital: 0.421,
          magic_formula_rank: 2,
          reproduction_value_per_share: 55.18,
          epv_per_share: 110.03,
          epv_margin_of_safety: -0.74,
          traffic_light: 'GREEN',
          wc_anomaly: 'NORMAL',
        },
        {
          rank: 3,
          ticker: 'GOOGL',
          company_name: 'Alphabet Inc.',
          sector: 'Communication Services',
          sic_code: 7370,
          price: 178.10,
          market_cap: 2210000000000,
          enterprise_value: 2110000000000,
          ebit: 95000000000,
          earnings_yield: 0.045,
          return_on_capital: 0.365,
          magic_formula_rank: 3,
          reproduction_value_per_share: 30.65,
          epv_per_share: 57.46,
          epv_margin_of_safety: -0.68,
          traffic_light: 'GREEN',
          wc_anomaly: 'NORMAL',
        },
        {
          rank: 4,
          ticker: 'TXN',
          company_name: 'Texas Instruments Inc.',
          sector: 'Semiconductors',
          sic_code: 3674,
          price: 195.40,
          market_cap: 178000000000,
          enterprise_value: 182000000000,
          ebit: 6500000000,
          earnings_yield: 0.0357,
          return_on_capital: 0.285,
          magic_formula_rank: 4,
          reproduction_value_per_share: 35.13,
          epv_per_share: 53.51,
          epv_margin_of_safety: -0.72,
          traffic_light: 'YELLOW',
          wc_anomaly: 'NORMAL',
        },
      ]);
      setSource('DEMO');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchResults();
  }, [minCap, sortBy, sortOrder, selectedSector]);

  // Client-side quick filter for text search
  const filteredItems = useMemo(() => {
    if (!search.trim()) return items;
    const q = search.toLowerCase().trim();
    return items.filter(
      (item) =>
        item.ticker.toLowerCase().includes(q) ||
        item.company_name.toLowerCase().includes(q) ||
        item.sector.toLowerCase().includes(q)
    );
  }, [items, search]);

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-terminal-bg select-none">
      {/* 1. Terminal Header */}
      <Header
        onRefresh={fetchResults}
        isLoading={isLoading}
        itemCount={filteredItems.length}
        source={source}
      />

      {/* 2. Top Controls & Filters */}
      <Toolbar
        search={search}
        onSearchChange={setSearch}
        minCap={minCap}
        onMinCapChange={setMinCap}
        sortBy={sortBy}
        onSortByChange={setSortBy}
        sortOrder={sortOrder}
        onToggleSortOrder={() => setSortOrder((prev) => (prev === 'asc' ? 'desc' : 'asc'))}
        selectedSector={selectedSector}
        onSectorChange={setSelectedSector}
      />

      {/* 3. Main Data-Dense Table */}
      <main className="flex-1 flex overflow-hidden relative">
        <ScreenerTable
          items={filteredItems}
          selectedTicker={selectedTicker}
          onSelectTicker={(t) => setSelectedTicker(t)}
          isLoading={isLoading}
        />

        {/* 4. Company Detail Drawer */}
        <CompanyDrawer
          ticker={selectedTicker}
          onClose={() => setSelectedTicker(null)}
        />
      </main>

      {/* Footer / Status bar */}
      <footer className="bg-terminal-panel border-t border-terminal-border px-3 py-1 flex items-center justify-between text-[10px] text-terminal-muted">
        <div>
          <span className="text-terminal-cyan font-bold mr-1">FRAMEWORKS:</span>
          <span>GREENBLATT MAGIC FORMULA • BRUCE GREENWALD EPV • STEADY-STATE DCF</span>
        </div>
        <div className="hidden sm:block">
          <span>PRESS ANY ROW FOR FULL 10-K XBRL FACT AUDIT</span>
        </div>
      </footer>
    </div>
  );
};
