'use client';

import { ProtectedRoute } from '@/components/protected-route';
import { LayoutWrapper } from '@/components/layout-wrapper';
import { useState, useEffect } from 'react';
import { AlertTriangle, TrendingDown, Shield, Activity, RefreshCw } from 'lucide-react';
import { KellyStatsCard } from '@/components/dashboard/KellyStatsCard';

interface RiskMetrics {
  portfolio_heat: number;
  portfolio_heat_pct: number;
  max_heat_limit: number;
  heat_utilization: number;
  daily_pl: number;
  daily_pl_pct: number;
  daily_loss_limit: number;
  drawdown: number;
  max_drawdown_limit: number;
  peak_equity: number;
  circuit_breaker_status: 'normal' | 'warning' | 'triggered';
  circuit_breaker_reason: string | null;
  num_positions: number;
}

export default function RiskManagementPage() {
  return (
    <ProtectedRoute>
      <LayoutWrapper>
        <RiskManagementContent />
      </LayoutWrapper>
    </ProtectedRoute>
  );
}

function RiskManagementContent() {
  const [riskMetrics, setRiskMetrics] = useState<RiskMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [resetting, setResetting] = useState(false);

  const fetchRiskMetrics = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/bot/risk-metrics?bot=quantshift-equity');
      if (!response.ok) throw new Error('Failed to fetch risk metrics');
      const data = await response.json();
      setRiskMetrics(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const resetCircuitBreaker = async () => {
    if (!confirm('Are you sure you want to reset the circuit breaker? Only do this after reviewing the situation.')) {
      return;
    }

    try {
      setResetting(true);
      const response = await fetch('/api/bot/reset-circuit-breaker?bot=quantshift-equity', {
        method: 'POST',
      });
      if (!response.ok) throw new Error('Failed to reset circuit breaker');
      await fetchRiskMetrics();
      alert('Circuit breaker reset successfully');
    } catch (err) {
      alert(`Failed to reset circuit breaker: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setResetting(false);
    }
  };

  useEffect(() => {
    fetchRiskMetrics();
    const interval = setInterval(fetchRiskMetrics, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  if (loading && !riskMetrics) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-slate-400">Loading risk metrics...</div>
      </div>
    );
  }

  if (error && !riskMetrics) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-red-400">Error: {error}</div>
      </div>
    );
  }

  if (!riskMetrics) return null;

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'triggered': return 'bg-red-500';
      case 'warning': return 'bg-yellow-500';
      default: return 'bg-green-500';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'triggered': return 'TRIGGERED';
      case 'warning': return 'WARNING';
      default: return 'NORMAL';
    }
  };

  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Risk Management</h1>
          <p className="text-slate-400">Portfolio-level risk controls and circuit breakers</p>
        </div>
        <button
          onClick={fetchRiskMetrics}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Circuit Breaker Status */}
      <div className={`p-6 rounded-xl border ${
        riskMetrics.circuit_breaker_status === 'triggered' 
          ? 'bg-red-900/20 border-red-500' 
          : riskMetrics.circuit_breaker_status === 'warning'
          ? 'bg-yellow-900/20 border-yellow-500'
          : 'bg-green-900/20 border-green-500'
      }`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className={`h-4 w-4 rounded-full ${getStatusColor(riskMetrics.circuit_breaker_status)} animate-pulse`} />
            <div>
              <h2 className="text-xl font-bold text-white">
                Circuit Breaker: {getStatusText(riskMetrics.circuit_breaker_status)}
              </h2>
              {riskMetrics.circuit_breaker_reason && (
                <p className="text-slate-300 mt-1">{riskMetrics.circuit_breaker_reason}</p>
              )}
            </div>
          </div>
          {riskMetrics.circuit_breaker_status === 'triggered' && (
            <button
              onClick={resetCircuitBreaker}
              disabled={resetting}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors disabled:opacity-50"
            >
              {resetting ? 'Resetting...' : 'Reset Circuit Breaker'}
            </button>
          )}
        </div>
      </div>

      {/* Risk Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Portfolio Heat */}
        <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="h-10 w-10 bg-orange-600/20 rounded-lg flex items-center justify-center">
              <Activity className="h-5 w-5 text-orange-400" />
            </div>
            <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Portfolio Heat</h3>
          </div>
          <div className="space-y-2">
            <div className="text-3xl font-bold text-white">
              {(riskMetrics.portfolio_heat_pct * 100).toFixed(1)}%
            </div>
            <div className="text-sm text-slate-400">
              Limit: {(riskMetrics.max_heat_limit * 100).toFixed(0)}%
            </div>
            <div className="w-full bg-slate-700 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all ${
                  riskMetrics.heat_utilization > 0.8 ? 'bg-red-500' : 
                  riskMetrics.heat_utilization > 0.6 ? 'bg-yellow-500' : 
                  'bg-green-500'
                }`}
                style={{ width: `${Math.min(riskMetrics.heat_utilization * 100, 100)}%` }}
              />
            </div>
            <div className="text-xs text-slate-500">
              {(riskMetrics.heat_utilization * 100).toFixed(0)}% utilized
            </div>
          </div>
        </div>

        {/* Daily P&L */}
        <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className={`h-10 w-10 ${riskMetrics.daily_pl >= 0 ? 'bg-green-600/20' : 'bg-red-600/20'} rounded-lg flex items-center justify-center`}>
              <TrendingDown className={`h-5 w-5 ${riskMetrics.daily_pl >= 0 ? 'text-green-400 rotate-180' : 'text-red-400'}`} />
            </div>
            <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Daily P&L</h3>
          </div>
          <div className="space-y-2">
            <div className={`text-3xl font-bold ${riskMetrics.daily_pl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {riskMetrics.daily_pl >= 0 ? '+' : ''}${riskMetrics.daily_pl.toFixed(2)}
            </div>
            <div className="text-sm text-slate-400">
              {riskMetrics.daily_pl >= 0 ? '+' : ''}{(riskMetrics.daily_pl_pct * 100).toFixed(2)}%
            </div>
            <div className="text-xs text-slate-500">
              Limit: -{(riskMetrics.daily_loss_limit * 100).toFixed(0)}%
            </div>
          </div>
        </div>

        {/* Drawdown */}
        <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="h-10 w-10 bg-purple-600/20 rounded-lg flex items-center justify-center">
              <AlertTriangle className="h-5 w-5 text-purple-400" />
            </div>
            <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Drawdown</h3>
          </div>
          <div className="space-y-2">
            <div className="text-3xl font-bold text-white">
              {(riskMetrics.drawdown * 100).toFixed(2)}%
            </div>
            <div className="text-sm text-slate-400">
              Limit: {(riskMetrics.max_drawdown_limit * 100).toFixed(0)}%
            </div>
            <div className="w-full bg-slate-700 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all ${
                  riskMetrics.drawdown / riskMetrics.max_drawdown_limit > 0.8 ? 'bg-red-500' : 
                  riskMetrics.drawdown / riskMetrics.max_drawdown_limit > 0.6 ? 'bg-yellow-500' : 
                  'bg-green-500'
                }`}
                style={{ width: `${Math.min((riskMetrics.drawdown / riskMetrics.max_drawdown_limit) * 100, 100)}%` }}
              />
            </div>
            <div className="text-xs text-slate-500">
              Peak: ${riskMetrics.peak_equity?.toFixed(2) || '0.00'}
            </div>
          </div>
        </div>

        {/* Open Positions */}
        <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="h-10 w-10 bg-cyan-600/20 rounded-lg flex items-center justify-center">
              <Shield className="h-5 w-5 text-cyan-400" />
            </div>
            <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Open Positions</h3>
          </div>
          <div className="space-y-2">
            <div className="text-3xl font-bold text-white">
              {riskMetrics.num_positions}
            </div>
            <div className="text-sm text-slate-400">
              Active trades
            </div>
          </div>
        </div>
      </div>

      {/* Kelly Criterion Stats - Phase 5 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <KellyStatsCard botName="quantshift-equity" />
      </div>

      {/* Risk Limits Information */}
      <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6">
        <h2 className="text-xl font-bold text-white mb-4">Risk Limits & Controls</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Portfolio Heat</h3>
            <p className="text-slate-300 text-sm mb-2">
              Maximum total portfolio risk exposure from all open positions.
            </p>
            <ul className="text-sm text-slate-400 space-y-1">
              <li>• Limit: {(riskMetrics.max_heat_limit * 100).toFixed(0)}% of account equity</li>
              <li>• Current: {(riskMetrics.portfolio_heat_pct * 100).toFixed(1)}%</li>
              <li>• Blocks new trades if limit exceeded</li>
            </ul>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Daily Loss Limit</h3>
            <p className="text-slate-300 text-sm mb-2">
              Maximum allowed loss in a single trading day.
            </p>
            <ul className="text-sm text-slate-400 space-y-1">
              <li>• Limit: {(riskMetrics.daily_loss_limit * 100).toFixed(0)}% of starting equity</li>
              <li>• Current: {(Math.abs(riskMetrics.daily_pl_pct) * 100).toFixed(2)}%</li>
              <li>• Triggers circuit breaker if exceeded</li>
            </ul>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Max Drawdown</h3>
            <p className="text-slate-300 text-sm mb-2">
              Maximum allowed decline from peak equity.
            </p>
            <ul className="text-sm text-slate-400 space-y-1">
              <li>• Limit: {(riskMetrics.max_drawdown_limit * 100).toFixed(0)}% from peak</li>
              <li>• Current: {(riskMetrics.drawdown * 100).toFixed(2)}%</li>
              <li>• Triggers circuit breaker if exceeded</li>
            </ul>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Circuit Breaker</h3>
            <p className="text-slate-300 text-sm mb-2">
              Automatic trading halt when risk limits are breached.
            </p>
            <ul className="text-sm text-slate-400 space-y-1">
              <li>• Blocks all new trade signals</li>
              <li>• Existing positions remain open</li>
              <li>• Requires manual reset after review</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Warning Message */}
      {riskMetrics.circuit_breaker_status === 'warning' && (
        <div className="bg-yellow-900/20 border border-yellow-500 rounded-xl p-6">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-6 w-6 text-yellow-400 flex-shrink-0 mt-1" />
            <div>
              <h3 className="text-lg font-bold text-yellow-400 mb-2">Warning: Approaching Risk Limits</h3>
              <p className="text-slate-300">
                {riskMetrics.circuit_breaker_reason}
              </p>
              <p className="text-slate-400 mt-2 text-sm">
                The bot is approaching risk limits. Monitor positions closely and consider reducing exposure.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Triggered Message */}
      {riskMetrics.circuit_breaker_status === 'triggered' && (
        <div className="bg-red-900/20 border border-red-500 rounded-xl p-6">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-6 w-6 text-red-400 flex-shrink-0 mt-1" />
            <div>
              <h3 className="text-lg font-bold text-red-400 mb-2">Circuit Breaker Triggered - Trading Halted</h3>
              <p className="text-slate-300 mb-4">
                {riskMetrics.circuit_breaker_reason}
              </p>
              <div className="bg-slate-800 rounded-lg p-4 space-y-2">
                <p className="text-white font-semibold">Action Required:</p>
                <ol className="text-slate-300 text-sm space-y-1 list-decimal list-inside">
                  <li>Review open positions and market conditions</li>
                  <li>Check bot logs for details on what triggered the breaker</li>
                  <li>Assess if it's safe to resume trading</li>
                  <li>Only reset the circuit breaker after thorough review</li>
                </ol>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
