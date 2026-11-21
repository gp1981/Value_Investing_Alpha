import React, { useEffect, useState } from 'react';
import {
  X,
  Award,
  Layers,
  TrendingUp,
  ShieldCheck,
  Grid3X3,
  FileText,
  ExternalLink,
  Maximize2,
  Minimize2,
  Table,
  GitCompare,
  Search,
  BookOpen,
  ArrowRight,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import {
  CompanyDetailResponse,
  CompanyStatementsResponse,
  StatementReport,
  FilingContentResponse,
  FilingDiffResponse
} from '../types';

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

const formatCurrencyFull = (val?: number | null) => {
  if (val === null || val === undefined || isNaN(val)) return '—';
  return `$${Math.round(val).toLocaleString()}`;
};

const formatPercent = (val?: number | null) => {
  if (val === null || val === undefined || isNaN(val)) return '—';
  return `${(val * 100).toFixed(2)}%`;
};

export const CompanyDrawer: React.FC<CompanyDrawerProps> = ({ ticker, onClose }) => {
  // Main view state
  const [data, setData] = useState<CompanyDetailResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isExpanded, setIsExpanded] = useState<boolean>(false);
  const [activeMainTab, setActiveMainTab] = useState<'OVERVIEW' | 'STATEMENTS' | 'FILING_VIEWER' | 'FILING_DIFF'>('OVERVIEW');

  // Manual Width Resizing State (default to 50% of webpage width)
  const [drawerWidth, setDrawerWidth] = useState<number>(() => {
    if (typeof window !== 'undefined') {
      return Math.max(640, Math.round(window.innerWidth * 0.5));
    }
    return 720;
  });
  const [isDragging, setIsDragging] = useState<boolean>(false);

  // Drag resize handler
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging) return;
      const newWidth = window.innerWidth - e.clientX;
      const minWidth = 480;
      const maxWidth = window.innerWidth - 60;
      if (newWidth >= minWidth && newWidth <= maxWidth) {
        setDrawerWidth(newWidth);
      }
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    if (isDragging) {
      document.body.style.cursor = 'ew-resize';
      document.body.style.userSelect = 'none';
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
    } else {
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    }

    return () => {
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging]);

  // Filings overview list filter
  const [filingFilter, setFilingFilter] = useState<'ALL' | '10-K' | '10-Q' | '8-K'>('ALL');

  // Multi-Period Statements State
  const [statements, setStatements] = useState<CompanyStatementsResponse | null>(null);
  const [isStatementsLoading, setIsStatementsLoading] = useState(false);
  const [activeStatementTab, setActiveStatementTab] = useState<'IS' | 'BS' | 'CF'>('IS');
  const [showFullNumbers, setShowFullNumbers] = useState<boolean>(false);

  // In-Platform Filing Viewer State
  const [selectedAccession, setSelectedAccession] = useState<string>('');
  const [selectedSection, setSelectedSection] = useState<string>('Item 1');
  const [filingContent, setFilingContent] = useState<FilingContentResponse | null>(null);
  const [isFilingLoading, setIsFilingLoading] = useState(false);
  const [filingSearch, setFilingSearch] = useState<string>('');

  // Redline Diff State
  const [diffForm, setDiffForm] = useState<'10-K' | '10-Q'>('10-K');
  const [diffAcc1, setDiffAcc1] = useState<string>('');
  const [diffAcc2, setDiffAcc2] = useState<string>('');
  const [diffSection, setDiffSection] = useState<string>('Item 1');
  const [diffResult, setDiffResult] = useState<FilingDiffResponse | null>(null);
  const [isDiffLoading, setIsDiffLoading] = useState(false);
  const [diffError, setDiffError] = useState<string | null>(null);

  // Load Overview Data when ticker changes
  useEffect(() => {
    if (!ticker) {
      setData(null);
      setStatements(null);
      setFilingContent(null);
      setDiffResult(null);
      return;
    }

    const fetchDetails = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const res = await fetch(`/api/company/${ticker}`);
        if (!res.ok) throw new Error(`Failed to load details for ${ticker}`);
        const json: CompanyDetailResponse = await res.json();
        setData(json);

        // Pre-select latest 10-K accession for reader and diff
        const tenKs = (json.filings || []).filter(f => f.form === '10-K');
        if (tenKs.length > 0) {
          setSelectedAccession(tenKs[0].accession_number);
          setDiffAcc1(tenKs[0].accession_number);
          if (tenKs.length > 1) {
            setDiffAcc2(tenKs[1].accession_number);
          }
        } else if (json.filings && json.filings.length > 0) {
          setSelectedAccession(json.filings[0].accession_number);
        }
      } catch (err: any) {
        setError(err.message || 'Error fetching company valuation data');
      } finally {
        setIsLoading(false);
      }
    };

    fetchDetails();
  }, [ticker]);

  // Load Multi-Period Financial Statements when entering STATEMENTS tab
  useEffect(() => {
    if (activeMainTab === 'STATEMENTS' && ticker && !statements && !isStatementsLoading) {
      const fetchStatements = async () => {
        setIsStatementsLoading(true);
        try {
          const res = await fetch(`/api/company/${ticker}/statements`);
          if (res.ok) {
            const json = await res.json();
            setStatements(json);
          }
        } catch {
          // Fallback handled in render
        } finally {
          setIsStatementsLoading(false);
        }
      };
      fetchStatements();
    }
  }, [activeMainTab, ticker, statements, isStatementsLoading]);

  // Load Filing Content when accession or section changes
  useEffect(() => {
    if (activeMainTab === 'FILING_VIEWER' && ticker && selectedAccession) {
      const fetchFilingDoc = async () => {
        setIsFilingLoading(true);
        try {
          const secParam = selectedSection ? `?section=${encodeURIComponent(selectedSection)}` : '';
          const res = await fetch(`/api/company/${ticker}/filing/${selectedAccession}${secParam}`);
          if (res.ok) {
            const json = await res.json();
            setFilingContent(json);
          }
        } catch {
          // Handled in render
        } finally {
          setIsFilingLoading(false);
        }
      };
      fetchFilingDoc();
    }
  }, [activeMainTab, ticker, selectedAccession, selectedSection]);

  // Execute Redline Diff
  const runRedlineDiff = async () => {
    if (!ticker || !diffAcc1 || !diffAcc2) return;
    setIsDiffLoading(true);
    setDiffError(null);
    try {
      const res = await fetch(`/api/company/${ticker}/filing-diff`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          form: diffForm,
          accession_1: diffAcc1,
          accession_2: diffAcc2,
          section: diffSection
        })
      });
      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || 'Failed to compute filing diff');
      }
      const json: FilingDiffResponse = await res.json();
      setDiffResult(json);
    } catch (err: any) {
      setDiffError(err.message || 'Error calculating redline comparison');
    } finally {
      setIsDiffLoading(false);
    }
  };

  if (!ticker) return null;

  // Valuation computations
  const shares = data?.shares_outstanding || 1;
  const price = data?.price || 1;
  const ebit = data?.magic_formula.ebit || 0;
  const normalizedTaxRate = data?.greenwald.tax_rate || 0.25;
  const normalizedEarnings = ebit * (1 - normalizedTaxRate);
  const epvWaccSteps = [0.08, 0.09, 0.10, 0.11, 0.12];
  const dcfDiscountRates = [0.08, 0.09, 0.10];
  const dcfGrowthRates = [0.015, 0.02, 0.025];
  const fcf = (data?.financial_statement?.net_income || 0) +
    (data?.financial_statement?.depreciation_amortization || 0) -
    (data?.financial_statement?.capex || 0);

  // Filtered filings list for Overview
  const filteredFilings = (data?.filings || []).filter((f) => {
    if (filingFilter === 'ALL') return true;
    return f.form === filingFilter;
  });

  // Current Statement Table to show
  const currentStatementReport: StatementReport | null | undefined =
    activeStatementTab === 'IS' ? statements?.income_statement :
    activeStatementTab === 'BS' ? statements?.balance_sheet :
    statements?.cash_flow;

  return (
    <div
      className={`fixed inset-y-0 right-0 bg-terminal-panel border-l border-terminal-border z-30 shadow-2xl flex flex-col font-mono text-xs select-none transition-all duration-300 ${
        isExpanded ? 'w-full sm:w-[94vw] lg:w-[1240px]' : 'w-full sm:w-[620px]'
      }`}
    >
      {/* 1. Master Title Header */}
      <div className="border-b border-terminal-border p-2.5 flex items-center justify-between bg-terminal-card">
        <div className="flex items-center gap-3">
          <span className="text-base font-bold text-terminal-green tracking-wider">{ticker}</span>
          <span className="text-terminal-muted truncate max-w-[280px] sm:max-w-[400px]">
            {data?.company_name || (isLoading ? 'SYNCING EDGAR & T3 STORAGE...' : 'TERMINAL WORKSPACE')}
          </span>
          {data?.sic_code && (
            <span className="hidden sm:inline-block px-1.5 py-0.5 rounded bg-terminal-border text-[10px] text-terminal-muted">
              SIC {data.sic_code}
            </span>
          )}
        </div>
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            title={isExpanded ? 'Dock to Side Panel' : 'Expand Full Workstation'}
            className="p-1 rounded text-terminal-muted hover:text-terminal-cyan hover:bg-terminal-border transition-colors"
          >
            {isExpanded ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
          </button>
          <button
            onClick={onClose}
            className="p-1 rounded text-terminal-muted hover:text-terminal-text hover:bg-terminal-border transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* 2. Top Animated Progress Pulse Bar */}
      {(isLoading || isStatementsLoading || isFilingLoading || isDiffLoading) && (
        <div className="w-full h-0.5 bg-terminal-border overflow-hidden">
          <div className="w-full h-full bg-gradient-to-r from-terminal-green via-terminal-cyan to-terminal-green animate-pulse" />
        </div>
      )}

      {/* 3. Terminal Navigation Tabs */}
      <div className="flex items-center justify-between border-b border-terminal-border bg-terminal-bg px-2 pt-1">
        <div className="flex items-center gap-1 overflow-x-auto no-scrollbar">
          <button
            onClick={() => setActiveMainTab('OVERVIEW')}
            className={`px-3 py-1.5 rounded-t text-[11px] font-semibold flex items-center gap-1.5 transition-colors ${
              activeMainTab === 'OVERVIEW'
                ? 'bg-terminal-card text-terminal-green border-t-2 border-terminal-green'
                : 'text-terminal-muted hover:text-terminal-text hover:bg-terminal-panel'
            }`}
          >
            <Award className="w-3 h-3 text-terminal-green" />
            <span>VALUATION // OVERVIEW</span>
          </button>

          <button
            onClick={() => setActiveMainTab('STATEMENTS')}
            className={`px-3 py-1.5 rounded-t text-[11px] font-semibold flex items-center gap-1.5 transition-colors ${
              activeMainTab === 'STATEMENTS'
                ? 'bg-terminal-card text-terminal-cyan border-t-2 border-terminal-cyan'
                : 'text-terminal-muted hover:text-terminal-text hover:bg-terminal-panel'
            }`}
          >
            <Table className="w-3 h-3 text-terminal-cyan" />
            <span>FINANCIALS (MULTI-YEAR)</span>
          </button>

          <button
            onClick={() => setActiveMainTab('FILING_VIEWER')}
            className={`px-3 py-1.5 rounded-t text-[11px] font-semibold flex items-center gap-1.5 transition-colors ${
              activeMainTab === 'FILING_VIEWER'
                ? 'bg-terminal-card text-terminal-amber border-t-2 border-terminal-amber'
                : 'text-terminal-muted hover:text-terminal-text hover:bg-terminal-panel'
            }`}
          >
            <BookOpen className="w-3 h-3 text-terminal-amber" />
            <span>SEC FILING READER</span>
          </button>

          <button
            onClick={() => setActiveMainTab('FILING_DIFF')}
            className={`px-3 py-1.5 rounded-t text-[11px] font-semibold flex items-center gap-1.5 transition-colors ${
              activeMainTab === 'FILING_DIFF'
                ? 'bg-terminal-card text-purple-400 border-t-2 border-purple-400'
                : 'text-terminal-muted hover:text-terminal-text hover:bg-terminal-panel'
            }`}
          >
            <GitCompare className="w-3 h-3 text-purple-400" />
            <span>REDLINE FILING DIFF</span>
          </button>
        </div>
      </div>

      {/* 4. Tab Body Area */}
      <div className="flex-1 overflow-y-auto p-3 sm:p-4 space-y-4">
        {error && (
          <div className="p-3 bg-red-950/40 border border-red-800/50 rounded text-terminal-red flex items-center gap-2">
            <AlertCircle className="w-4 h-4" />
            <span>{error}</span>
          </div>
        )}

        {/* =========================================================================
            TAB 1: OVERVIEW & VALUATION
           ========================================================================= */}
        {activeMainTab === 'OVERVIEW' && data && (
          <div className="space-y-4">
            {/* Quick Metrics Header Pill */}
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

            {/* Grid 2-columns if expanded, 1-col if side panel */}
            <div className={`grid gap-4 ${isExpanded ? 'grid-cols-2' : 'grid-cols-1'}`}>
              {/* Magic Formula Card */}
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

              {/* Greenwald EPV & Moat Card */}
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

                {/* EPV Sensitivity */}
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

              {/* Steady-State DCF */}
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
                    <span>DCF MATRIX (DISCOUNT RATE vs PERPETUAL GROWTH):</span>
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

              {/* Solvency & Safety Audit */}
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
            </div>

            {/* Recent SEC Filings Quick List */}
            <div className="border border-terminal-border bg-terminal-card rounded p-3 space-y-2">
              <div className="flex items-center justify-between border-b border-terminal-border pb-1.5">
                <div className="flex items-center gap-1.5 text-terminal-cyan font-semibold">
                  <FileText className="w-3.5 h-3.5 text-terminal-cyan" />
                  <span>
                    RECENT REGULATORY FILINGS (
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

              {(!data.filings || filteredFilings.length === 0) ? (
                <div className="py-4 text-center text-terminal-muted text-[10px]">
                  No {filingFilter} filings found in local SEC repository.
                </div>
              ) : (
                <div className="max-h-56 overflow-y-auto divide-y divide-terminal-border/30 text-[10px]">
                  {filteredFilings.map((filing) => {
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
                            {/* Quick open in in-platform reader tab */}
                            <button
                              onClick={() => {
                                setSelectedAccession(filing.accession_number);
                                setActiveMainTab('FILING_VIEWER');
                              }}
                              className="px-1.5 py-0.5 rounded bg-terminal-green/15 text-terminal-green hover:bg-terminal-green/25 border border-terminal-green/40 transition-colors font-medium text-[9px]"
                            >
                              OPEN IN READER
                            </button>
                            {filing.interactive_url && (
                              <a
                                href={filing.interactive_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-terminal-cyan/15 text-terminal-cyan hover:bg-terminal-cyan/25 border border-terminal-cyan/40 transition-colors font-medium text-[9px]"
                                title="Open Official SEC Interactive Data Viewer"
                              >
                                <span>XBRL</span>
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
                                <span>INDEX</span>
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

            {/* Raw XBRL Line Items Snapshot */}
            <div className="border border-terminal-border bg-terminal-card rounded p-3 space-y-2">
              <span className="text-[10px] text-terminal-muted uppercase tracking-wider block border-b border-terminal-border pb-1">
                SEC XBRL FILING DATA POINTS (TTM BASELINE)
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
          </div>
        )}

        {/* =========================================================================
            TAB 2: MULTI-YEAR FINANCIAL STATEMENTS (BS, IS, CF)
           ========================================================================= */}
        {activeMainTab === 'STATEMENTS' && (
          <div className="space-y-3">
            {/* Sub-Tabs: Income Statement vs Balance Sheet vs Cash Flow */}
            <div className="flex items-center justify-between bg-terminal-card p-2 rounded border border-terminal-border">
              <div className="flex items-center gap-1.5">
                {(['IS', 'BS', 'CF'] as const).map((stmt) => (
                  <button
                    key={stmt}
                    onClick={() => setActiveStatementTab(stmt)}
                    className={`px-3 py-1 rounded text-xs font-bold transition-colors ${
                      activeStatementTab === stmt
                        ? 'bg-terminal-cyan text-terminal-bg font-extrabold'
                        : 'bg-terminal-bg text-terminal-muted hover:text-terminal-text border border-terminal-border'
                    }`}
                  >
                    {stmt === 'IS' ? 'INCOME STATEMENT' : stmt === 'BS' ? 'BALANCE SHEET' : 'CASH FLOW'}
                  </button>
                ))}
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowFullNumbers(!showFullNumbers)}
                  className="px-2 py-1 rounded border border-terminal-border text-[10px] text-terminal-muted hover:text-terminal-text hover:bg-terminal-bg"
                >
                  FORMAT: {showFullNumbers ? 'EXACT ($)' : 'COMPACT ($B/M)'}
                </button>
              </div>
            </div>

            {isStatementsLoading ? (
              <div className="flex flex-col items-center justify-center py-24 text-terminal-muted space-y-2">
                <div className="animate-spin w-6 h-6 border-2 border-terminal-cyan border-t-transparent rounded-full" />
                <span>EXTRACTING MULTI-YEAR EDGAR XBRL STATEMENTS...</span>
              </div>
            ) : !currentStatementReport || currentStatementReport.rows.length === 0 ? (
              <div className="p-8 text-center text-terminal-muted border border-terminal-border rounded bg-terminal-card">
                No multi-period {activeStatementTab} statements found for {ticker} in repository.
              </div>
            ) : (
              <div className="border border-terminal-border rounded bg-terminal-card overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-[11px] tabular-numbers border-collapse">
                    <thead>
                      <tr className="bg-terminal-bg border-b border-terminal-border text-terminal-muted">
                        <th className="py-1.5 px-3 text-left font-bold w-[45%]">LINE ITEM (US-GAAP)</th>
                        {currentStatementReport.periods.map((period) => (
                          <th key={period} className="py-1.5 px-3 text-right font-bold">
                            {period}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-terminal-border/20">
                      {currentStatementReport.rows.map((row, idx) => {
                        const indentPx = Math.min(row.depth * 14, 48);
                        const isHeader = row.is_abstract;
                        const isTotal = row.is_total;

                        return (
                          <tr
                            key={idx}
                            className={`hover:bg-terminal-bg/60 transition-colors ${
                              isHeader
                                ? 'bg-terminal-border/30 text-terminal-cyan font-bold'
                                : isTotal
                                ? 'bg-terminal-bg/40 font-bold border-t border-b border-terminal-border'
                                : 'text-terminal-text'
                            }`}
                          >
                            <td className="py-1 px-3 text-left truncate" style={{ paddingLeft: `${12 + indentPx}px` }}>
                              <span className={isTotal ? 'text-terminal-green font-bold' : ''}>
                                {row.label}
                              </span>
                            </td>
                            {currentStatementReport.periods.map((period) => {
                              const val = row.values[period];
                              return (
                                <td
                                  key={period}
                                  className={`py-1 px-3 text-right whitespace-nowrap ${
                                    isTotal ? 'font-bold text-terminal-text' : 'text-terminal-muted'
                                  }`}
                                >
                                  {isHeader ? '' : showFullNumbers ? formatCurrencyFull(val) : formatCurrencyCompact(val)}
                                </td>
                              );
                            })}
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {/* =========================================================================
            TAB 3: IN-PLATFORM SEC FILING VIEWER
           ========================================================================= */}
        {activeMainTab === 'FILING_VIEWER' && (
          <div className="space-y-3">
            {/* Filing Selector Controls Bar */}
            <div className="bg-terminal-card p-3 rounded border border-terminal-border space-y-2">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                <div>
                  <label className="text-[10px] text-terminal-muted block mb-1">SELECT FILING TO READ:</label>
                  <select
                    value={selectedAccession}
                    onChange={(e) => setSelectedAccession(e.target.value)}
                    className="w-full bg-terminal-bg border border-terminal-border rounded px-2 py-1 text-xs text-terminal-text focus:outline-none focus:border-terminal-cyan"
                  >
                    {(data?.filings || []).map((f) => (
                      <option key={f.accession_number} value={f.accession_number}>
                        {f.form} // {f.filing_date} ({f.accession_number})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="text-[10px] text-terminal-muted block mb-1">SELECT ITEM / SECTION:</label>
                  <select
                    value={selectedSection}
                    onChange={(e) => setSelectedSection(e.target.value)}
                    className="w-full bg-terminal-bg border border-terminal-border rounded px-2 py-1 text-xs text-terminal-text focus:outline-none focus:border-terminal-cyan"
                  >
                    <option value="">FULL DOCUMENT TEXT</option>
                    {(filingContent?.available_sections || []).map((sec) => (
                      <option key={sec} value={sec}>
                        {sec}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Text Search & External link */}
              <div className="flex items-center justify-between pt-1 border-t border-terminal-border/40">
                <div className="flex items-center gap-1.5 w-full max-w-sm">
                  <Search className="w-3.5 h-3.5 text-terminal-muted" />
                  <input
                    type="text"
                    placeholder="Search words in section..."
                    value={filingSearch}
                    onChange={(e) => setFilingSearch(e.target.value)}
                    className="bg-terminal-bg border border-terminal-border rounded px-2 py-0.5 text-xs text-terminal-text placeholder-terminal-muted/60 w-full focus:outline-none focus:border-terminal-cyan"
                  />
                </div>
                {filingContent?.sec_url && (
                  <a
                    href={filingContent.sec_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 text-[10px] text-terminal-cyan hover:underline"
                  >
                    <span>SEC EDGAR INDEX</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                )}
              </div>
            </div>

            {/* Document Content Display Container */}
            {isFilingLoading ? (
              <div className="flex flex-col items-center justify-center py-24 text-terminal-muted space-y-2">
                <div className="animate-spin w-6 h-6 border-2 border-terminal-amber border-t-transparent rounded-full" />
                <span>EXTRACTING FILING SECTION FROM SEC REPOSITORY...</span>
              </div>
            ) : !filingContent ? (
              <div className="p-8 text-center text-terminal-muted border border-terminal-border rounded bg-terminal-card">
                Select a filing above to read sections directly in this terminal.
              </div>
            ) : (
              <div className="border border-terminal-border rounded bg-terminal-card p-4 space-y-2">
                <div className="flex items-center justify-between border-b border-terminal-border pb-2 text-[10px]">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded font-bold bg-amber-950 text-amber-400 border border-amber-600/50">
                      {filingContent.form}
                    </span>
                    <span className="text-terminal-text font-bold">
                      {filingContent.selected_section || 'DOCUMENT TEXT'}
                    </span>
                    <span className="text-terminal-muted">Filed {filingContent.filing_date}</span>
                  </div>
                  <span className="text-terminal-muted font-mono">{filingContent.accession_number}</span>
                </div>

                <div className="max-h-[540px] overflow-y-auto text-[11px] leading-relaxed text-terminal-text font-mono whitespace-pre-wrap select-text p-2 bg-terminal-bg rounded border border-terminal-border/40">
                  {filingSearch
                    ? filingContent.content
                        .split(new RegExp(`(${filingSearch})`, 'gi'))
                        .map((part, i) =>
                          part.toLowerCase() === filingSearch.toLowerCase() ? (
                            <mark key={i} className="bg-yellow-500/40 text-yellow-200 px-0.5 rounded font-bold">
                              {part}
                            </mark>
                          ) : (
                            part
                          )
                        )
                    : filingContent.content}
                </div>
              </div>
            )}
          </div>
        )}

        {/* =========================================================================
            TAB 4: REDLINE FILING DIFF (YEAR-OVER-YEAR COMPARISON)
           ========================================================================= */}
        {activeMainTab === 'FILING_DIFF' && (
          <div className="space-y-3">
            {/* Diff Setup Controls */}
            <div className="bg-terminal-card p-3 rounded border border-terminal-border space-y-3">
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-2">
                <div>
                  <label className="text-[10px] text-terminal-muted block mb-1">FORM TYPE:</label>
                  <select
                    value={diffForm}
                    onChange={(e) => setDiffForm(e.target.value as any)}
                    className="w-full bg-terminal-bg border border-terminal-border rounded px-2 py-1 text-xs text-terminal-text focus:outline-none focus:border-purple-400"
                  >
                    <option value="10-K">10-K (Annual)</option>
                    <option value="10-Q">10-Q (Quarterly)</option>
                  </select>
                </div>

                <div>
                  <label className="text-[10px] text-terminal-muted block mb-1">NEWER FILING (CURRENT):</label>
                  <select
                    value={diffAcc1}
                    onChange={(e) => setDiffAcc1(e.target.value)}
                    className="w-full bg-terminal-bg border border-terminal-border rounded px-2 py-1 text-xs text-terminal-text focus:outline-none focus:border-purple-400"
                  >
                    {(data?.filings || [])
                      .filter((f) => f.form === diffForm)
                      .map((f) => (
                        <option key={f.accession_number} value={f.accession_number}>
                          {f.filing_date} ({f.accession_number})
                        </option>
                      ))}
                  </select>
                </div>

                <div>
                  <label className="text-[10px] text-terminal-muted block mb-1">PRIOR FILING (HISTORIC):</label>
                  <select
                    value={diffAcc2}
                    onChange={(e) => setDiffAcc2(e.target.value)}
                    className="w-full bg-terminal-bg border border-terminal-border rounded px-2 py-1 text-xs text-terminal-text focus:outline-none focus:border-purple-400"
                  >
                    {(data?.filings || [])
                      .filter((f) => f.form === diffForm)
                      .map((f) => (
                        <option key={f.accession_number} value={f.accession_number}>
                          {f.filing_date} ({f.accession_number})
                        </option>
                      ))}
                  </select>
                </div>

                <div>
                  <label className="text-[10px] text-terminal-muted block mb-1">SECTION TO COMPARE:</label>
                  <select
                    value={diffSection}
                    onChange={(e) => setDiffSection(e.target.value)}
                    className="w-full bg-terminal-bg border border-terminal-border rounded px-2 py-1 text-xs text-terminal-text focus:outline-none focus:border-purple-400"
                  >
                    <option value="Item 1">Item 1 (Business)</option>
                    <option value="Item 1A">Item 1A (Risk Factors)</option>
                    <option value="Item 7">Item 7 (MD&A)</option>
                    <option value="Item 3">Item 3 (Legal Proceedings)</option>
                    <option value="Item 8">Item 8 (Financial Statements)</option>
                  </select>
                </div>
              </div>

              <div className="flex items-center justify-between pt-1 border-t border-terminal-border/40">
                <div className="text-[10px] text-terminal-muted">
                  Runs word-level SequenceMatcher to detect modifications, additions, and deletions between fiscal filings.
                </div>
                <button
                  onClick={runRedlineDiff}
                  disabled={isDiffLoading || !diffAcc1 || !diffAcc2}
                  className="px-3 py-1 rounded bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs flex items-center gap-1.5 transition-colors disabled:opacity-50"
                >
                  <GitCompare className="w-3.5 h-3.5" />
                  <span>{isDiffLoading ? 'COMPARING...' : 'RUN REDLINE DIFF'}</span>
                </button>
              </div>
            </div>

            {diffError && (
              <div className="p-3 bg-red-950/40 border border-red-800/50 rounded text-terminal-red">
                {diffError}
              </div>
            )}

            {/* Diff Result Container */}
            {isDiffLoading ? (
              <div className="flex flex-col items-center justify-center py-24 text-terminal-muted space-y-2">
                <div className="animate-spin w-6 h-6 border-2 border-purple-400 border-t-transparent rounded-full" />
                <span>COMPUTING WORD-LEVEL REDLINE COMPARISON...</span>
              </div>
            ) : !diffResult ? (
              <div className="p-8 text-center text-terminal-muted border border-terminal-border rounded bg-terminal-card space-y-1">
                <div>Select two filings and a section above, then click <strong>RUN REDLINE DIFF</strong>.</div>
                <div className="text-[10px]">Identifies product additions, legal changes, and new risk factor disclosures over time.</div>
              </div>
            ) : (
              <div className="border border-terminal-border rounded bg-terminal-card p-3 space-y-3">
                {/* Statistics Bar */}
                <div className="flex items-center justify-between p-2 rounded bg-terminal-bg border border-terminal-border">
                  <div className="flex items-center gap-3">
                    <span className="font-bold text-terminal-text">{diffResult.section} COMPARISON</span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        diffResult.similarity_pct > 80
                          ? 'bg-emerald-950 text-emerald-400 border border-emerald-600/50'
                          : diffResult.similarity_pct > 60
                          ? 'bg-amber-950 text-amber-400 border border-amber-600/50'
                          : 'bg-rose-950 text-rose-400 border border-rose-600/50'
                      }`}
                    >
                      {diffResult.similarity_pct}% SIMILARITY
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-[10px]">
                    <span className="px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-300 border border-emerald-600/50 font-bold">
                      +{diffResult.words_added} WORDS ADDED
                    </span>
                    <span className="px-2 py-0.5 rounded bg-rose-950/60 text-rose-300 border border-rose-600/50 font-bold">
                      -{diffResult.words_removed} WORDS REMOVED
                    </span>
                  </div>
                </div>

                {/* Token Stream Text Area */}
                <div className="max-h-[500px] overflow-y-auto p-3 rounded bg-terminal-bg border border-terminal-border/40 text-[11px] font-mono leading-relaxed select-text whitespace-pre-wrap">
                  {diffResult.tokens.map((token, i) => {
                    if (token.type === 'equal') {
                      return <span key={i} className="text-terminal-text">{token.text} </span>;
                    } else if (token.type === 'added') {
                      return (
                        <span
                          key={i}
                          className="bg-emerald-950/80 text-emerald-300 font-bold px-1 py-0.5 rounded border border-emerald-600/60 mx-0.5 inline-block"
                          title="Added in newer filing"
                        >
                          {token.text}{' '}
                        </span>
                      );
                    } else {
                      return (
                        <span
                          key={i}
                          className="bg-rose-950/80 text-rose-300 line-through px-1 py-0.5 rounded border border-rose-700/60 mx-0.5 inline-block opacity-80"
                          title="Removed from prior filing"
                        >
                          {token.text}{' '}
                        </span>
                      );
                    }
                  })}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
