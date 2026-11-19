import React, { useState } from 'react';
import { X, Lock, Mail, User, CheckCircle2, AlertCircle } from 'lucide-react';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAuthSuccess: (token: string, user: any) => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose, onAuthSuccess }) => {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    const endpoint = isRegister ? '/api/auth/register' : '/api/auth/login';
    const body = isRegister
      ? { email, password, full_name: fullName }
      : { email, password };

    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Authentication failed');
      }

      onAuthSuccess(data.access_token, data.user);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Authentication error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleUseDemo = () => {
    setEmail('analyst@example.com');
    setPassword('valuealpha2026');
    setIsRegister(false);
  };

  return (
    <div className="fixed inset-0 bg-black/75 backdrop-blur-xs flex items-center justify-center z-50 p-4 font-mono select-none">
      <div className="w-full max-w-sm bg-terminal-panel border border-terminal-border rounded shadow-2xl overflow-hidden text-xs">
        {/* Header */}
        <div className="border-b border-terminal-border bg-terminal-card p-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Lock className="w-4 h-4 text-terminal-green" />
            <span className="font-bold text-terminal-text tracking-wider uppercase">
              {isRegister ? 'REGISTER ANALYST' : 'TERMINAL LOGIN'}
            </span>
          </div>
          <button onClick={onClose} className="text-terminal-muted hover:text-terminal-text transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-4 space-y-3">
          {error && (
            <div className="flex items-center gap-2 bg-red-950/40 border border-red-800/50 p-2 rounded text-terminal-red text-[11px]">
              <AlertCircle className="w-3.5 h-3.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {isRegister && (
            <div>
              <label className="text-[10px] text-terminal-muted uppercase block mb-1">Full Name</label>
              <div className="relative">
                <User className="w-3.5 h-3.5 text-terminal-muted absolute left-2.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="e.g. Seth Klarman"
                  className="w-full bg-terminal-bg border border-terminal-border rounded pl-8 pr-2 py-1.5 text-terminal-text focus:outline-none focus:border-terminal-cyan"
                />
              </div>
            </div>
          )}

          <div>
            <label className="text-[10px] text-terminal-muted uppercase block mb-1">Email Address</label>
            <div className="relative">
              <Mail className="w-3.5 h-3.5 text-terminal-muted absolute left-2.5 top-1/2 -translate-y-1/2" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="analyst@example.com"
                className="w-full bg-terminal-bg border border-terminal-border rounded pl-8 pr-2 py-1.5 text-terminal-text focus:outline-none focus:border-terminal-cyan"
              />
            </div>
          </div>

          <div>
            <label className="text-[10px] text-terminal-muted uppercase block mb-1">Password</label>
            <div className="relative">
              <Lock className="w-3.5 h-3.5 text-terminal-muted absolute left-2.5 top-1/2 -translate-y-1/2" />
              <input
                type="password"
                required
                minLength={6}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-terminal-bg border border-terminal-border rounded pl-8 pr-2 py-1.5 text-terminal-text focus:outline-none focus:border-terminal-cyan"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full mt-2 bg-terminal-green/20 hover:bg-terminal-green/30 text-terminal-green border border-terminal-green/50 py-1.5 rounded font-bold uppercase transition-colors disabled:opacity-50"
          >
            {isLoading ? 'AUTHENTICATING...' : isRegister ? 'CREATE ACCOUNT' : 'ENTER TERMINAL'}
          </button>

          {/* Demo Account Quick-Fill */}
          {!isRegister && (
            <div className="text-center pt-1">
              <button
                type="button"
                onClick={handleUseDemo}
                className="text-[10px] text-terminal-muted hover:text-terminal-cyan underline underline-offset-2 transition-colors"
              >
                Auto-fill pre-seeded demo analyst account
              </button>
            </div>
          )}

          {/* Toggle Register / Login */}
          <div className="border-t border-terminal-border pt-2 text-center text-[10px] text-terminal-muted">
            {isRegister ? (
              <span>
                Already registered?{' '}
                <button
                  type="button"
                  onClick={() => { setIsRegister(false); setError(null); }}
                  className="text-terminal-cyan hover:underline font-bold"
                >
                  Sign In
                </button>
              </span>
            ) : (
              <span>
                Need access?{' '}
                <button
                  type="button"
                  onClick={() => { setIsRegister(true); setError(null); }}
                  className="text-terminal-cyan hover:underline font-bold"
                >
                  Create Account
                </button>
              </span>
            )}
          </div>
        </form>
      </div>
    </div>
  );
};
