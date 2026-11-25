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
  AlertCircle,
  Calendar,
  Paperclip,
  Bookmark,
  Bell,
  Scale,
  UserCheck
} from 'lucide-react';
import {
  CompanyDetailResponse,
  CompanyStatementsResponse,
  StatementReport,
  FilingContentResponse,
  FilingDiffResponse,
  SECFilingItem,
  EdgarFormItem,
  InsiderRadarResponse,
  MaterialEventsResponse,
  GovernanceResponse,
  FilingSearchResponse
} from '../types';
import { FilingContentRenderer } from './FilingContentRenderer';

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
  const [activeMainTab, setActiveMainTab] = useState<'OVERVIEW' | 'STATEMENTS' | 'FILING_VIEWER' | 'FILING_DIFF' | 'INSIDERS' | 'EVENTS_GOV'>('OVERVIEW');

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
  const [edgarForms, setEdgarForms] = useState<EdgarFormItem[]>([]);
  const [readerForm, setReaderForm] = useState<string>('ALL');
  const [readerPeriod, setReaderPeriod] = useState<string>('last_5_years');
  const [readerStartDate, setReaderStartDate] = useState<string>('');
  const [readerEndDate, setReaderEndDate] = useState<string>('');
  const [readerFilings, setReaderFilings] = useState<SECFilingItem[]>([]);
  const [isReaderFilingsLoading, setIsReaderFilingsLoading] = useState<boolean>(false);
  const [selectedAccession, setSelectedAccession] = useState<string>('');
  const [selectedSection, setSelectedSection] = useState<string>('Item 1');
  const [filingContent, setFilingContent] = useState<FilingContentResponse | null>(null);
  const [isFilingLoading, setIsFilingLoading] = useState(false);
  const [filingSearch, setFilingSearch] = useState<string>('');
  const [fullTextQuery, setFullTextQuery] = useState<string>('');
  const [fullTextResults, setFullTextResults] = useState<FilingSearchResponse | null>(null);
  const [isFullTextSearching, setIsFullTextSearching] = useState<boolean>(false);

  // Stage 2: Insiders (Form 4) & Events / Governance (8-K / DEF 14A)
  const [insiderData, setInsiderData] = useState<InsiderRadarResponse | null>(null);
  const [isInsiderLoading, setIsInsiderLoading] = useState<boolean>(false);
  const [eventsData, setEventsData] = useState<MaterialEventsResponse | null>(null);
  const [governanceData, setGovernanceData] = useState<GovernanceResponse | null>(null);
  const [isEventsGovLoading, setIsEventsGovLoading] = useState<boolean>(false);

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
      setInsiderData(null);
      setEventsData(null);
      setGovernanceData(null);
      setFullTextResults(null);
      setReaderFilings([]);
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

  // Load EDGAR form catalog once
  useEffect(() => {
    fetch('/api/company/edgar-forms')
      .then((r) => r.json())
      .then((d) => {
        if (Array.isArray(d?.forms)) setEdgarForms(d.forms);
      })
      .catch(() => {});
  }, []);

  // Load filtered filings list when entering FILING_VIEWER or changing filters
  useEffect(() => {
    if (activeMainTab === 'FILING_VIEWER' && ticker) {
      const params = new URLSearchParams({ limit: '60' });
      if (readerForm !== 'ALL') params.set('forms', readerForm);
      if (readerPeriod !== 'custom') {
        params.set('period', readerPeriod);
      } else {
        if (readerStartDate) params.set('start_date', readerStartDate);
        if (readerEndDate) params.set('end_date', readerEndDate);
      }
      setIsReaderFilingsLoading(true);
      fetch(`/api/company/${ticker}/filings?${params.toString()}`)
        .then((r) => r.json())
        .then((list: SECFilingItem[]) => {
          if (Array.isArray(list)) {
            setReaderFilings(list);
            if (list.length > 0 && !list.some((f) => f.accession_number === selectedAccession)) {
              setSelectedAccession(list[0].accession_number);
            }
          }
        })
        .catch(() => {})
        .finally(() => setIsReaderFilingsLoading(false));
    }
  }, [activeMainTab, ticker, readerForm, readerPeriod, readerStartDate, readerEndDate]);

  // Load Form 4 Insider Radar when entering INSIDERS tab
  useEffect(() => {
    if (activeMainTab === 'INSIDERS' && ticker && !insiderData && !isInsiderLoading) {
      setIsInsiderLoading(true);
      fetch(`/api/company/${ticker}/insider-trades`)
        .then((r) => (r.ok ? r.json() : null))
        .then((d) => d && setInsiderData(d))
        .catch(() => {})
        .finally(() => setIsInsiderLoading(false));
    }
  }, [activeMainTab, ticker, insiderData, isInsiderLoading]);

  // Load 8-K Material Events & DEF 14A Governance when entering EVENTS_GOV tab
  useEffect(() => {
    if (activeMainTab === 'EVENTS_GOV' && ticker && !eventsData && !isEventsGovLoading) {
      setIsEventsGovLoading(true);
      Promise.all([
        fetch(`/api/company/${ticker}/material-events`).then((r) => (r.ok ? r.json() : null)),
        fetch(`/api/company/${ticker}/governance`).then((r) => (r.ok ? r.json() : null)),
      ])
        .then(([ev, gov]) => {
          if (ev) setEventsData(ev);
          if (gov) setGovernanceData(gov);
        })
        .catch(() => {})
        .finally(() => setIsEventsGovLoading(false));
    }
  }, [activeMainTab, ticker, eventsData, isEventsGovLoading]);

  const runFullTextSearch = async () => {
    if (!ticker || fullTextQuery.trim().length < 2) return;
    setIsFullTextSearching(true);
    try {
      const res = await fetch(`/api/company/${ticker}/search-filing`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: fullTextQuery.trim(),
          form: readerForm !== 'ALL' ? readerForm : '10-K',
          accession_number: selectedAccession || null,
        }),
      });
      if (res.ok) {
        setFullTextResults(await res.json());
      }
    } catch {
      // ignore
    } finally {
      setIsFullTextSearching(false);
    }
  };

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
      className="fixed inset-y-0 right-0 bg-terminal-panel border-l border-terminal-border z-30 shadow-2xl flex flex-col font-mono text-xs select-none"
      style={{ width: isExpanded ? '94vw' : drawerWidth }}
    >
      {/* Drag Resize Handle */}
      <div
        onMouseDown={() => setIsDragging(true)}
        className="absolute left-0 top-0 bottom-0 w-1.5 cursor-ew-resize hover:bg-terminal-cyan/40 transition-colors z-50"
        title="Drag to resize panel"
      />
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
            <span>REDLINE DIFF</span>
          </button>

          <button
            onClick={() => setActiveMainTab('INSIDERS')}
            className={`px-3 py-1.5 rounded-t text-[11px] font-semibold flex items-center gap-1.5 transition-colors ${
              activeMainTab === 'INSIDERS'
                ? 'bg-terminal-card text-emerald-400 border-t-2 border-emerald-400'
                : 'text-terminal-muted hover:text-terminal-text hover:bg-terminal-panel'
            }`}
          >
            <UserCheck className="w-3 h-3 text-emerald-400" />
            <span>INSIDERS (FORM 4)</span>
          </button>

          <button
            onClick={() => setActiveMainTab('EVENTS_GOV')}
            className={`px-3 py-1.5 rounded-t text-[11px] font-semibold flex items-center gap-1.5 transition-colors ${
              activeMainTab === 'EVENTS_GOV'
                ? 'bg-terminal-card text-rose-400 border-t-2 border-rose-400'
                : 'text-terminal-muted hover:text-terminal-text hover:bg-terminal-panel'
            }`}
          >
            <Bell className="w-3 h-3 text-rose-400" />
            <span>8-K &amp; PROXY</span>
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
            TAB 3: IN-PLATFORM SEC FILING VIEWER (ENHANCED WITH FILTERS, BOOKMARKS & TABLES)
           ========================================================================= */}
        {activeMainTab === 'FILING_VIEWER' && (
          <div className="space-y-3">
            {/* 1. Search & Filter Bar (Form Type + Period Preset / Date Range) */}
            <div className="bg-terminal-card p-3 rounded border border-terminal-border space-y-2.5">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                <div>
                  <label className="text-[10px] text-terminal-muted block mb-1">FORM TYPE (EDGAR DATA OBJECT):</label>
                  <select
                    value={readerForm}
                    onChange={(e) => setReaderForm(e.target.value)}
                    className="w-full bg-terminal-bg border border-terminal-border rounded px-2 py-1 text-xs text-terminal-text focus:outline-none focus:border-terminal-cyan"
                  >
                    <option value="ALL">ALL FORMS (10-K, 10-Q, 8-K, DEF 14A, 4)</option>
                    {(edgarForms.length > 0 ? edgarForms : [
                      { form: '10-K', object_name: 'TenK', category: 'Financials', description: 'Annual Report' },
                      { form: '10-Q', object_name: 'TenQ', category: 'Financials', description: 'Quarterly Report' },
                      { form: '8-K', object_name: 'CurrentReport', category: 'Events', description: 'Current Report' },
                      { form: 'DEF 14A', object_name: 'ProxyStatement', category: 'Governance', description: 'Proxy Statement' },
                      { form: '4', object_name: 'Ownership', category: 'Insiders', description: 'Insider Trading' },
                      { form: '13F-HR', object_name: 'ThirteenF', category: 'Ownership', description: 'Institutional Holdings' },
                    ]).map((ef) => (
                      <option key={ef.form} value={ef.form} title={ef.description}>
                        {ef.form} ({ef.object_name}) — {ef.description.split('—')[0].trim()}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="text-[10px] text-terminal-muted flex items-center gap-1 mb-1">
                    <Calendar className="w-3 h-3" /> TIMEFRAME:
                  </label>
                  <select
                    value={readerPeriod}
                    onChange={(e) => setReaderPeriod(e.target.value)}
                    className="w-full bg-terminal-bg border border-terminal-border rounded px-2 py-1 text-xs text-terminal-text focus:outline-none focus:border-terminal-cyan"
                  >
                    <option value="last_quarter">Last Quarter (90d)</option>
                    <option value="last_4_quarters">Last 4 Quarters (1Y)</option>
                    <option value="last_year">Last Year</option>
                    <option value="last_5_years">Last 5 Years</option>
                    <option value="all">All Available</option>
                    <option value="custom">Custom Date Range...</option>
                  </select>
                </div>

                <div>
                  <label className="text-[10px] text-terminal-muted block mb-1">IN-SECTION HIGHLIGHT:</label>
                  <div className="flex items-center gap-1.5">
                    <Search className="w-3.5 h-3.5 text-terminal-muted shrink-0" />
                    <input
                      type="text"
                      placeholder="Highlight in current view..."
                      value={filingSearch}
                      onChange={(e) => setFilingSearch(e.target.value)}
                      className="bg-terminal-bg border border-terminal-border rounded px-2 py-1 text-xs text-terminal-text placeholder-terminal-muted/60 w-full focus:outline-none focus:border-terminal-cyan"
                    />
                  </div>
                </div>
              </div>

              {readerPeriod === 'custom' && (
                <div className="grid grid-cols-2 gap-2 pt-1 border-t border-terminal-border/40">
                  <div>
                    <label className="text-[10px] text-terminal-muted block mb-0.5">FROM DATE:</label>
                    <input
                      type="date"
                      value={readerStartDate}
                      onChange={(e) => setReaderStartDate(e.target.value)}
                      className="w-full bg-terminal-bg border border-terminal-border rounded px-2 py-1 text-xs text-terminal-text"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] text-terminal-muted block mb-0.5">TO DATE:</label>
                    <input
                      type="date"
                      value={readerEndDate}
                      onChange={(e) => setReaderEndDate(e.target.value)}
                      className="w-full bg-terminal-bg border border-terminal-border rounded px-2 py-1 text-xs text-terminal-text"
                    />
                  </div>
                </div>
              )}

              {/* Scrollable Filing Selector List */}
              <div className="pt-1 border-t border-terminal-border/40">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] text-terminal-muted">
                    MATCHING FILINGS ({readerFilings.length}) {isReaderFilingsLoading ? '— LOADING...' : ''}
                  </span>
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
                <div className="max-h-28 overflow-y-auto border border-terminal-border rounded bg-terminal-bg divide-y divide-terminal-border/30">
                  {readerFilings.length === 0 ? (
                    <div className="p-2 text-center text-terminal-muted text-[11px]">
                      {isReaderFilingsLoading ? 'Querying SEC EDGAR filings...' : 'No filings match selected filter.'}
                    </div>
                  ) : (
                    readerFilings.map((f) => {
                      const active = f.accession_number === selectedAccession;
                      return (
                        <button
                          key={f.accession_number}
                          onClick={() => setSelectedAccession(f.accession_number)}
                          className={`w-full text-left px-2.5 py-1 flex items-center justify-between text-[11px] transition-colors ${
                            active ? 'bg-terminal-card text-terminal-amber font-bold' : 'hover:bg-terminal-card/50 text-terminal-text'
                          }`}
                        >
                          <div className="flex items-center gap-2 truncate">
                            <span className="px-1.5 py-0.2 rounded bg-terminal-border text-[10px] text-terminal-cyan font-bold">
                              {f.form}
                            </span>
                            <span>{f.filing_date}</span>
                            <span className="text-terminal-muted truncate">{f.description}</span>
                          </div>
                          <span className="text-[10px] text-terminal-muted font-mono shrink-0 ml-2">{f.accession_number}</span>
                        </button>
                      );
                    })
                  )}
                </div>
              </div>

              {/* Full-Text Filing Search */}
              <div className="flex items-center gap-2 pt-1 border-t border-terminal-border/40">
                <input
                  type="text"
                  placeholder="Full-text search across all sections of this filing (e.g. 'material weakness', 'lease')..."
                  value={fullTextQuery}
                  onChange={(e) => setFullTextQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && runFullTextSearch()}
                  className="bg-terminal-bg border border-terminal-border rounded px-2 py-1 text-xs text-terminal-text placeholder-terminal-muted/60 flex-1 focus:outline-none focus:border-terminal-amber"
                />
                <button
                  onClick={runFullTextSearch}
                  disabled={isFullTextSearching || fullTextQuery.trim().length < 2}
                  className="px-2.5 py-1 rounded bg-amber-600/80 hover:bg-amber-500 text-white font-bold text-[11px] disabled:opacity-50"
                >
                  {isFullTextSearching ? 'SEARCHING...' : 'SEARCH FILING'}
                </button>
              </div>

              {fullTextResults && (
                <div className="p-2 rounded bg-terminal-bg border border-amber-700/40 space-y-1 max-h-36 overflow-y-auto">
                  <div className="flex items-center justify-between text-[10px] text-amber-300 font-bold">
                    <span>{fullTextResults.total_hits} HITS FOR &quot;{fullTextResults.query}&quot;</span>
                    <button onClick={() => setFullTextResults(null)} className="text-terminal-muted hover:text-terminal-text">CLEAR</button>
                  </div>
                  {fullTextResults.hits.map((h, idx) => (
                    <div key={idx} className="text-[10.5px] border-t border-terminal-border/30 pt-1">
                      <span className="text-terminal-cyan font-bold">[{h.section}]</span>{' '}
                      <span className="text-terminal-muted">{h.snippet}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* 2. Main Reader Layout: Left Section Bookmarks + Right Document & Attachments */}
            {isFilingLoading ? (
              <div className="flex flex-col items-center justify-center py-24 text-terminal-muted space-y-2">
                <div className="animate-spin w-6 h-6 border-2 border-terminal-amber border-t-transparent rounded-full" />
                <span>EXTRACTING STRUCTURED FILING &amp; TABLES FROM SEC...</span>
              </div>
            ) : !filingContent ? (
              <div className="p-8 text-center text-terminal-muted border border-terminal-border rounded bg-terminal-card">
                Select a filing above to read sections and tables directly in this terminal.
              </div>
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-4 gap-3">
                {/* Left Sidebar: Section Bookmarks + Attachments */}
                <div className="lg:col-span-1 space-y-3">
                  <div className="border border-terminal-border rounded bg-terminal-card overflow-hidden">
                    <div className="px-2.5 py-1.5 bg-terminal-bg border-b border-terminal-border flex items-center gap-1.5 text-[10px] font-bold text-terminal-amber">
                      <Bookmark className="w-3 h-3" />
                      <span>SECTION BOOKMARKS</span>
                    </div>
                    <div className="max-h-72 overflow-y-auto divide-y divide-terminal-border/30">
                      <button
                        onClick={() => setSelectedSection('')}
                        className={`w-full text-left px-2.5 py-1.5 text-[11px] transition-colors ${
                          selectedSection === '' ? 'bg-terminal-bg text-terminal-amber font-bold' : 'text-terminal-muted hover:text-terminal-text'
                        }`}
                      >
                        FULL DOCUMENT OVERVIEW
                      </button>
                      {(filingContent.section_bookmarks && filingContent.section_bookmarks.length > 0
                        ? filingContent.section_bookmarks
                        : (filingContent.available_sections || []).map((s) => ({ id: s, title: s }))
                      ).map((bm) => (
                        <button
                          key={bm.id}
                          onClick={() => setSelectedSection(bm.id)}
                          className={`w-full text-left px-2.5 py-1.5 text-[11px] transition-colors ${
                            selectedSection === bm.id
                              ? 'bg-terminal-bg text-terminal-amber font-bold border-l-2 border-terminal-amber'
                              : 'text-terminal-muted hover:text-terminal-text hover:bg-terminal-bg/40'
                          }`}
                        >
                          {bm.title}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Attachments / Exhibits */}
                  {filingContent.attachments && filingContent.attachments.length > 0 && (
                    <div className="border border-terminal-border rounded bg-terminal-card overflow-hidden">
                      <div className="px-2.5 py-1.5 bg-terminal-bg border-b border-terminal-border flex items-center gap-1.5 text-[10px] font-bold text-terminal-cyan">
                        <Paperclip className="w-3 h-3" />
                        <span>ATTACHMENTS ({filingContent.attachments.length})</span>
                      </div>
                      <div className="max-h-56 overflow-y-auto divide-y divide-terminal-border/30">
                        {filingContent.attachments.map((att, idx) => (
                          <a
                            key={idx}
                            href={att.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="block px-2.5 py-1.5 hover:bg-terminal-bg/60 transition-colors"
                          >
                            <div className="flex items-center justify-between text-[10.5px]">
                              <span className="text-terminal-cyan font-bold truncate">{att.doc_type || att.document}</span>
                              <ExternalLink className="w-2.5 h-2.5 text-terminal-muted shrink-0" />
                            </div>
                            <div className="text-[10px] text-terminal-muted truncate">{att.description || att.document}</div>
                          </a>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Right Main Reading Pane */}
                <div className="lg:col-span-3 border border-terminal-border rounded bg-terminal-card p-4 space-y-2">
                  <div className="flex items-center justify-between border-b border-terminal-border pb-2 text-[10px]">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded font-bold bg-amber-950 text-amber-400 border border-amber-600/50">
                        {filingContent.form}
                      </span>
                      <span className="text-terminal-text font-bold">
                        {(filingContent.section_bookmarks || []).find((b) => b.id === filingContent.selected_section)?.title ||
                          filingContent.selected_section ||
                          'FULL DOCUMENT'}
                      </span>
                      <span className="text-terminal-muted">Filed {filingContent.filing_date}</span>
                    </div>
                    <span className="text-terminal-muted font-mono">{filingContent.accession_number}</span>
                  </div>

                  <div className="max-h-[600px] overflow-y-auto p-3 bg-terminal-bg rounded border border-terminal-border/40">
                    <FilingContentRenderer content={filingContent.content} searchQuery={filingSearch} />
                  </div>
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
                    <option value="10-K">10-K (Annual Report)</option>
                    <option value="10-Q">10-Q (Quarterly Report)</option>
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
                    <option value="Item 1">Item 1 - Business</option>
                    <option value="Item 1A">Item 1A - Risk Factors</option>
                    <option value="Item 1C">Item 1C - Cybersecurity</option>
                    <option value="Item 3">Item 3 - Legal Proceedings</option>
                    <option value="Item 7">Item 7 - MD&amp;A</option>
                    <option value="Item 7A">Item 7A - Market Risk</option>
                    <option value="Item 8">Item 8 - Financial Statements</option>
                  </select>
                </div>
              </div>

              <div className="flex items-center justify-between pt-1 border-t border-terminal-border/40">
                <div className="text-[10px] text-terminal-muted">
                  Preserves paragraph &amp; table line structure while detecting word-level additions and deletions.
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

                <div className="max-h-[560px] overflow-y-auto p-3 rounded bg-terminal-bg border border-terminal-border/40 text-[11.5px] font-mono leading-relaxed select-text whitespace-pre-wrap">
                  {diffResult.tokens.map((token, i) => {
                    if (token.type === 'equal') {
                      return <span key={i} className="text-terminal-text">{token.text}</span>;
                    } else if (token.type === 'added') {
                      return (
                        <span
                          key={i}
                          className="bg-emerald-950/80 text-emerald-300 font-bold px-1 py-0.5 rounded border border-emerald-600/60 mx-0.5"
                          title="Added in newer filing"
                        >
                          {token.text}
                        </span>
                      );
                    } else {
                      return (
                        <span
                          key={i}
                          className="bg-rose-950/80 text-rose-300 line-through px-1 py-0.5 rounded border border-rose-700/60 mx-0.5 opacity-80"
                          title="Removed from prior filing"
                        >
                          {token.text}
                        </span>
                      );
                    }
                  })}
                </div>
              </div>
            )}
          </div>
        )}

        {/* =========================================================================
            TAB 5: STAGE 2 — INSIDER TRADING & CLUSTER BUYING RADAR (FORM 4)
           ========================================================================= */}
        {activeMainTab === 'INSIDERS' && (
          <div className="space-y-3">
            {isInsiderLoading ? (
              <div className="flex flex-col items-center justify-center py-24 text-terminal-muted space-y-2">
                <div className="animate-spin w-6 h-6 border-2 border-emerald-400 border-t-transparent rounded-full" />
                <span>PARSING FORM 4 INSIDER OWNERSHIP FILINGS...</span>
              </div>
            ) : !insiderData ? (
              <div className="p-6 text-center text-terminal-muted border border-terminal-border rounded bg-terminal-card">
                No Form 4 insider data available for {ticker}.
              </div>
            ) : (
              <>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 bg-terminal-card p-3 rounded border border-terminal-border">
                  <div>
                    <div className="text-[10px] text-terminal-muted">30-DAY CLUSTER SIGNAL</div>
                    {insiderData.cluster_buying_detected ? (
                      <span className="inline-block mt-1 px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-500 font-bold text-[11px]">
                        CLUSTER BUYING DETECTED ({insiderData.cluster_buyers_count} INSIDERS)
                      </span>
                    ) : (
                      <span className="inline-block mt-1 text-terminal-muted text-[11px]">
                        No 30d cluster ({insiderData.cluster_buyers_count} buyers)
                      </span>
                    )}
                  </div>
                  <div>
                    <div className="text-[10px] text-terminal-muted">OPEN MARKET PURCHASES (RECENT)</div>
                    <div className="text-sm font-bold text-terminal-green tabular-numbers">
                      {formatCurrencyCompact(insiderData.total_purchases_usd)}
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] text-terminal-muted">OPEN MARKET SALES (RECENT)</div>
                    <div className="text-sm font-bold text-terminal-red tabular-numbers">
                      {formatCurrencyCompact(insiderData.total_sales_usd)}
                    </div>
                  </div>
                </div>

                <div className="border border-terminal-border rounded bg-terminal-card overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="w-full text-[11px] tabular-numbers border-collapse">
                      <thead>
                        <tr className="bg-terminal-bg border-b border-terminal-border text-terminal-muted">
                          <th className="py-1.5 px-2.5 text-left">DATE</th>
                          <th className="py-1.5 px-2.5 text-left">INSIDER</th>
                          <th className="py-1.5 px-2.5 text-center">CODE</th>
                          <th className="py-1.5 px-2.5 text-right">SHARES</th>
                          <th className="py-1.5 px-2.5 text-right">PRICE</th>
                          <th className="py-1.5 px-2.5 text-right">VALUE</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-terminal-border/30">
                        {insiderData.transactions.length === 0 ? (
                          <tr>
                            <td colSpan={6} className="p-4 text-center text-terminal-muted">No recent Form 4 transactions parsed.</td>
                          </tr>
                        ) : (
                          insiderData.transactions.map((tx, idx) => (
                            <tr key={idx} className="hover:bg-terminal-bg/60">
                              <td className="py-1 px-2.5 text-terminal-muted">{tx.transaction_date || tx.filing_date}</td>
                              <td className="py-1 px-2.5">
                                <div className="text-terminal-text font-bold">{tx.insider_name}</div>
                                {tx.title && <div className="text-[10px] text-terminal-muted truncate max-w-[180px]">{tx.title}</div>}
                              </td>
                              <td className="py-1 px-2.5 text-center">
                                <span
                                  className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                                    tx.transaction_code === 'P'
                                      ? 'bg-emerald-950 text-emerald-300 border border-emerald-600/50'
                                      : tx.transaction_code === 'S'
                                      ? 'bg-rose-950 text-rose-300 border border-rose-600/50'
                                      : 'bg-terminal-border text-terminal-muted'
                                  }`}
                                >
                                  {tx.transaction_code === 'P' ? 'BUY (P)' : tx.transaction_code === 'S' ? 'SELL (S)' : tx.transaction_code}
                                </span>
                              </td>
                              <td className="py-1 px-2.5 text-right">{tx.shares.toLocaleString()}</td>
                              <td className="py-1 px-2.5 text-right">{tx.price ? `$${tx.price.toFixed(2)}` : '—'}</td>
                              <td className="py-1 px-2.5 text-right font-bold">{tx.value_usd ? formatCurrencyCompact(tx.value_usd) : '—'}</td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </>
            )}
          </div>
        )}

        {/* =========================================================================
            TAB 6: STAGE 2 — FORM 8-K MATERIAL EVENTS & DEF 14A GOVERNANCE
           ========================================================================= */}
        {activeMainTab === 'EVENTS_GOV' && (
          <div className="space-y-4">
            {isEventsGovLoading ? (
              <div className="flex flex-col items-center justify-center py-24 text-terminal-muted space-y-2">
                <div className="animate-spin w-6 h-6 border-2 border-rose-400 border-t-transparent rounded-full" />
                <span>LOADING FORM 8-K EVENTS &amp; DEF 14A PROXY...</span>
              </div>
            ) : (
              <>
                {/* 8-K Material Events */}
                <div className="border border-terminal-border rounded bg-terminal-card p-3 space-y-2">
                  <div className="flex items-center gap-2 border-b border-terminal-border pb-1.5">
                    <Bell className="w-3.5 h-3.5 text-rose-400" />
                    <span className="font-bold text-terminal-text">FORM 8-K MATERIAL CORPORATE EVENTS</span>
                  </div>
                  {!eventsData || eventsData.events.length === 0 ? (
                    <div className="text-terminal-muted text-[11px] py-2">No recent Form 8-K filings found.</div>
                  ) : (
                    <div className="space-y-2">
                      {eventsData.events.map((ev, idx) => (
                        <div key={idx} className="p-2.5 rounded bg-terminal-bg border border-terminal-border/50 space-y-1">
                          <div className="flex items-center justify-between text-[10.5px]">
                            <span className="font-bold text-terminal-cyan">{ev.filing_date} // {ev.accession_number}</span>
                            {ev.sec_url && (
                              <a href={ev.sec_url} target="_blank" rel="noopener noreferrer" className="text-terminal-cyan hover:underline flex items-center gap-1">
                                <span>SEC 8-K</span> <ExternalLink className="w-2.5 h-2.5" />
                              </a>
                            )}
                          </div>
                          {ev.items.length > 0 && (
                            <div className="flex flex-wrap gap-1">
                              {ev.items.map((it, i) => (
                                <span key={i} className="px-1.5 py-0.5 rounded bg-rose-950/60 text-rose-300 border border-rose-700/40 text-[10px]">
                                  {it}
                                </span>
                              ))}
                            </div>
                          )}
                          {ev.summary && <div className="text-[11px] text-terminal-muted line-clamp-3">{ev.summary}</div>}
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* DEF 14A Proxy Governance */}
                <div className="border border-terminal-border rounded bg-terminal-card p-3 space-y-2">
                  <div className="flex items-center justify-between border-b border-terminal-border pb-1.5">
                    <div className="flex items-center gap-2">
                      <Scale className="w-3.5 h-3.5 text-terminal-amber" />
                      <span className="font-bold text-terminal-text">DEF 14A PROXY &amp; EXECUTIVE ALIGNMENT</span>
                    </div>
                    {governanceData?.sec_url && (
                      <a href={governanceData.sec_url} target="_blank" rel="noopener noreferrer" className="text-[10px] text-terminal-cyan hover:underline flex items-center gap-1">
                        <span>OPEN DEF 14A</span> <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>
                  {governanceData ? (
                    <div className="space-y-2">
                      <div className="text-[10.5px] text-terminal-muted">
                        Filed: <span className="text-terminal-text font-bold">{governanceData.filing_date || 'N/A'}</span> ({governanceData.accession_number})
                      </div>
                      <div className="max-h-72 overflow-y-auto p-2.5 rounded bg-terminal-bg border border-terminal-border/40">
                        <FilingContentRenderer content={governanceData.summary} />
                      </div>
                    </div>
                  ) : (
                    <div className="text-terminal-muted text-[11px]">No DEF 14A proxy summary available.</div>
                  )}
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
