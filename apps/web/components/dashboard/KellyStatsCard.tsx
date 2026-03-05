"use client";

import { useEffect, useState } from "react";
import { TrendingUp, Calculator, AlertCircle, CheckCircle } from "lucide-react";

interface KellyStats {
  enabled: boolean;
  kelly_percentage: number;
  kelly_fraction: number;
  min_trades_required: number;
  current_trades: number;
  win_rate: number;
  avg_win: number;
  avg_loss: number;
  recommended_size_pct: number;
  fallback_size_pct: number;
  using_fallback: boolean;
  reason: string;
}

export function KellyStatsCard({ botName }: { botName: string }) {
  const [kellyStats, setKellyStats] = useState<KellyStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchKellyStats();
    const interval = setInterval(fetchKellyStats, 60000);
    return () => clearInterval(interval);
  }, [botName]);

  const fetchKellyStats = async () => {
    try {
      const res = await fetch(`/api/bot/kelly-stats?botName=${botName}`);
      if (res.ok) {
        setKellyStats(await res.json());
      }
    } catch (error) {
      console.error('Failed to fetch Kelly stats:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700 animate-pulse">
        <div className="h-40 bg-slate-700/50 rounded" />
      </div>
    );
  }

  if (!kellyStats) {
    return (
      <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
        <p className="text-slate-400 text-sm">Kelly Criterion data unavailable</p>
      </div>
    );
  }

  const tradesProgress = Math.min((kellyStats.current_trades / kellyStats.min_trades_required) * 100, 100);
  const canUseKelly = kellyStats.current_trades >= kellyStats.min_trades_required;

  return (
    <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6">
      <div className="flex items-center gap-3 mb-4">
        <div className={`h-10 w-10 ${kellyStats.enabled && canUseKelly ? 'bg-blue-600/20' : 'bg-slate-600/20'} rounded-lg flex items-center justify-center`}>
          <Calculator className={`h-5 w-5 ${kellyStats.enabled && canUseKelly ? 'text-blue-400' : 'text-slate-400'}`} />
        </div>
        <div className="flex-1">
          <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Kelly Criterion</h3>
          <div className="flex items-center gap-2 mt-1">
            {kellyStats.enabled ? (
              canUseKelly ? (
                <span className="flex items-center gap-1 text-xs text-green-400">
                  <CheckCircle className="h-3 w-3" />
                  Active
                </span>
              ) : (
                <span className="flex items-center gap-1 text-xs text-yellow-400">
                  <AlertCircle className="h-3 w-3" />
                  Collecting Data
                </span>
              )
            ) : (
              <span className="text-xs text-slate-500">Disabled</span>
            )}
          </div>
        </div>
      </div>

      {!kellyStats.enabled ? (
        <div className="space-y-3">
          <p className="text-slate-400 text-sm">
            Kelly Criterion position sizing is disabled. Using fixed {(kellyStats.fallback_size_pct * 100).toFixed(1)}% risk per trade.
          </p>
          <div className="bg-slate-700/50 rounded-lg p-3">
            <p className="text-xs text-slate-400">
              Enable in config after {kellyStats.min_trades_required}+ trades for optimal position sizing.
            </p>
          </div>
        </div>
      ) : !canUseKelly ? (
        <div className="space-y-3">
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-400">Trade History</span>
              <span className="text-white font-semibold">
                {kellyStats.current_trades} / {kellyStats.min_trades_required}
              </span>
            </div>
            <div className="w-full bg-slate-700 rounded-full h-2">
              <div
                className="h-2 rounded-full bg-blue-500 transition-all"
                style={{ width: `${tradesProgress}%` }}
              />
            </div>
            <p className="text-xs text-slate-500">
              {kellyStats.min_trades_required - kellyStats.current_trades} more trades needed for Kelly calculation
            </p>
          </div>
          <div className="bg-yellow-900/20 border border-yellow-700/50 rounded-lg p-3">
            <p className="text-xs text-yellow-400">
              Using fallback: {(kellyStats.fallback_size_pct * 100).toFixed(1)}% fixed risk per trade
            </p>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Kelly Percentage */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-slate-400 text-sm">Kelly %</span>
              <span className="text-2xl font-bold text-blue-400">
                {(kellyStats.kelly_percentage * 100).toFixed(2)}%
              </span>
            </div>
            <p className="text-xs text-slate-500">
              Optimal position size based on edge and odds
            </p>
          </div>

          {/* Fractional Kelly */}
          <div className="bg-slate-700/50 rounded-lg p-3 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-slate-400 text-xs">Fractional Kelly</span>
              <span className="text-white text-sm font-semibold">
                {(kellyStats.kelly_fraction * 100).toFixed(0)}%
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400 text-xs">Recommended Size</span>
              <span className="text-green-400 text-sm font-semibold">
                {(kellyStats.recommended_size_pct * 100).toFixed(2)}%
              </span>
            </div>
          </div>

          {/* Statistics */}
          <div className="grid grid-cols-3 gap-3">
            <div>
              <p className="text-slate-500 text-xs">Win Rate</p>
              <p className="text-white text-sm font-semibold">
                {(kellyStats.win_rate * 100).toFixed(1)}%
              </p>
            </div>
            <div>
              <p className="text-slate-500 text-xs">Avg Win</p>
              <p className="text-green-400 text-sm font-semibold">
                ${kellyStats.avg_win.toFixed(2)}
              </p>
            </div>
            <div>
              <p className="text-slate-500 text-xs">Avg Loss</p>
              <p className="text-red-400 text-sm font-semibold">
                ${Math.abs(kellyStats.avg_loss).toFixed(2)}
              </p>
            </div>
          </div>

          {kellyStats.using_fallback && (
            <div className="bg-yellow-900/20 border border-yellow-700/50 rounded-lg p-3">
              <p className="text-xs text-yellow-400">
                ⚠️ {kellyStats.reason}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
