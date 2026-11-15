import React, { useState, useEffect } from 'react';
import { Activity, ShieldCheck, Database, Terminal, RefreshCw } from 'lucide-react';

interface HeaderProps {
  onRefresh: () => void;
  isLoading: boolean;
  itemCount: number;
  source: string;
}

export const Header: React.FC<HeaderProps> = ({ onRefresh, isLoading, itemCount, source }) => {
  const [time, setTime] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTime(now.toISOString().replace('T', ' ').substring(0, 19) + ' UTC');
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="border-b border-terminal-border bg-terminal-panel px-3 py-1.5 flex flex-wrap items-center justify-between gap-3 text-xs">
      {/* Title & Branding */}
      <div className="flex items-center gap-2.5">
        <div className="flex items-center gap-1.5 font-bold tracking-wider text-terminal-green">
          <Terminal className="w-4 h-4 text-terminal-green" />
          <span>ALPHA // TERMINAL</span>
        </div>
        <span className="text-[10px] uppercase tracking-widest text-terminal-muted bg-terminal-card px-1.5 py-0.5 rounded border border-terminal-border">
          SEC XBRL ENGINE
        </span>
      </div>

      {/* System Status Metrics */}
      <div className="flex items-center gap-4 text-[11px]">
        <div className="flex items-center gap-1.5 text-terminal-muted">
          <Database className="w-3.5 h-3.5 text-terminal-cyan" />
          <span>SOURCE:</span>
          <span className="text-terminal-text font-semibold uppercase">{source}</span>
        </div>

        <div className="flex items-center gap-1.5 text-terminal-muted">
          <Activity className="w-3.5 h-3.5 text-terminal-green" />
          <span>ACTIVE ROWS:</span>
          <span className="text-terminal-green font-semibold tabular-numbers">{itemCount}</span>
        </div>

        <div className="flex items-center gap-1.5 text-terminal-muted">
          <ShieldCheck className="w-3.5 h-3.5 text-terminal-amber" />
          <span>SYS:</span>
          <span className="text-terminal-text">ONLINE</span>
        </div>

        <div className="text-terminal-muted tabular-numbers border-l border-terminal-border pl-3 hidden md:inline-block">
          {time}
        </div>

        {/* Action Button */}
        <button
          onClick={onRefresh}
          disabled={isLoading}
          className="flex items-center gap-1 bg-terminal-card hover:bg-terminal-border text-terminal-text px-2 py-1 rounded border border-terminal-border transition-colors disabled:opacity-50"
          title="Refresh rankings"
        >
          <RefreshCw className={`w-3 h-3 ${isLoading ? 'animate-spin text-terminal-cyan' : ''}`} />
          <span>SYNC</span>
        </button>
      </div>
    </header>
  );
};
