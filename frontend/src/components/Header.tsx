import React, { useState, useEffect } from 'react';
import { Activity, ShieldCheck, Database, Terminal, RefreshCw, HardDrive, User, LogOut } from 'lucide-react';

interface HeaderProps {
  onRefresh: () => void;
  isLoading: boolean;
  itemCount: number;
  source: string;
  user: any;
  onOpenAuth: () => void;
  onLogout: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  onRefresh,
  isLoading,
  itemCount,
  source,
  user,
  onOpenAuth,
  onLogout,
}) => {
  const [time, setTime] = useState<string>('');
  const [storageInfo, setStorageInfo] = useState<{ sizeKb: number; count: number } | null>(null);

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTime(now.toISOString().replace('T', ' ').substring(0, 19) + ' UTC');
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    fetch('/health/storage')
      .then((res) => res.json())
      .then((data) => {
        setStorageInfo({
          sizeKb: data.cache_size_kb || 0,
          count: data.cached_tickers_count || 0,
        });
      })
      .catch(() => {});
  }, [isLoading]);

  return (
    <header className="border-b border-terminal-border bg-terminal-panel px-3 py-1.5 flex flex-wrap items-center justify-between gap-3 text-xs select-none">
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

      {/* System Status Metrics & User Auth */}
      <div className="flex items-center gap-3 text-[11px]">
        <div className="flex items-center gap-1.5 text-terminal-muted">
          <Database className="w-3.5 h-3.5 text-terminal-cyan" />
          <span>SOURCE:</span>
          <span className="text-terminal-text font-semibold uppercase">{source}</span>
        </div>

        {storageInfo && (
          <div className="hidden sm:flex items-center gap-1.5 text-terminal-muted" title={`Local cache size: ${storageInfo.sizeKb} KB`}>
            <HardDrive className="w-3.5 h-3.5 text-terminal-amber" />
            <span>CACHE:</span>
            <span className="text-terminal-text font-medium">{storageInfo.count > 0 ? `${storageInfo.count} STOCKS` : 'SYNC READY'}</span>
          </div>
        )}

        <div className="flex items-center gap-1.5 text-terminal-muted">
          <Activity className="w-3.5 h-3.5 text-terminal-green" />
          <span>DISPLAYED:</span>
          <span className="text-terminal-green font-semibold tabular-numbers">{itemCount}</span>
        </div>

        <div className="flex items-center gap-1.5 text-terminal-muted">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span>SYS:</span>
          <span className="text-terminal-text">ONLINE</span>
        </div>

        <div className="text-terminal-muted tabular-numbers border-l border-terminal-border pl-3 hidden xl:inline-block">
          {time}
        </div>

        {/* Sync Trigger */}
        <button
          onClick={onRefresh}
          disabled={isLoading}
          className="flex items-center gap-1 bg-terminal-card hover:bg-terminal-border text-terminal-text px-2 py-0.5 rounded border border-terminal-border transition-colors disabled:opacity-50"
          title="Refresh rankings"
        >
          <RefreshCw className={`w-3 h-3 ${isLoading ? 'animate-spin text-terminal-cyan' : ''}`} />
          <span>SYNC</span>
        </button>

        {/* User Authentication Pill / Button */}
        <div className="border-l border-terminal-border pl-2">
          {user ? (
            <div className="flex items-center gap-2 bg-terminal-card px-2 py-0.5 rounded border border-terminal-border">
              <User className="w-3 h-3 text-terminal-cyan" />
              <span className="text-terminal-text font-medium truncate max-w-[110px]" title={user.email}>
                {user.full_name || user.email.split('@')[0]}
              </span>
              <span className="text-[9px] bg-terminal-cyan/20 text-terminal-cyan border border-terminal-cyan/40 px-1 py-0.2 rounded font-bold">
                {user.tier || 'FREE'}
              </span>
              <button
                onClick={onLogout}
                className="text-terminal-muted hover:text-terminal-red ml-1 p-0.5 transition-colors"
                title="Sign Out"
              >
                <LogOut className="w-3 h-3" />
              </button>
            </div>
          ) : (
            <button
              onClick={onOpenAuth}
              className="flex items-center gap-1 bg-terminal-cyan/15 hover:bg-terminal-cyan/25 text-terminal-cyan border border-terminal-cyan/40 px-2.5 py-0.5 rounded font-bold uppercase transition-colors"
            >
              <User className="w-3 h-3" />
              <span>LOGIN</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
