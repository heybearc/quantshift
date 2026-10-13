'use client';

import { useEffect, useState } from 'react';

interface RegimeCurrent {
  regime: string;
  method: string;
  confidence: number | null;
  riskMultiplier: number;
  allocation: Record<string, number>;
  timestamp?: string;
  trend?: number | null;
  volatility?: number | null;
  marketBreadth?: number | null;
}

interface RegimeView {
  current: RegimeCurrent;
  stats: {
    totalChanges: number;
    averageConfidence: number;
    regimeDistribution: Record<string, number>;
  } | null;
  mlModel: {
    accuracy: number;
    trainDate?: string;
    features: Array<{ name: string; importance: number }>;
  } | null;
}

const regimeColors: Record<string, string> = {
  BULL_TRENDING: 'bg-green-500',
  BEAR_TRENDING: 'bg-red-500',
  HIGH_VOL_CHOPPY: 'bg-orange-500',
  LOW_VOL_RANGE: 'bg-blue-500',
  CRISIS: 'bg-purple-500',
  UNKNOWN: 'bg-gray-500',
};

const regimeLabels: Record<string, string> = {
  BULL_TRENDING: 'Bull Trending',
  BEAR_TRENDING: 'Bear Trending',
  HIGH_VOL_CHOPPY: 'High Vol Choppy',
  LOW_VOL_RANGE: 'Low Vol Range',
  CRISIS: 'Crisis',
  UNKNOWN: 'Unknown',
};

function finite(value: unknown): number | null {
  if (value == null || value === '') return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function readRegime(payload: Record<string, unknown>): RegimeView | null {
  const nested = payload.current;
  if (nested && typeof nested === 'object') {
    const current = nested as Record<string, unknown>;
    const regime = typeof current.regime === 'string' ? current.regime : '';
    if (!regime) return null;
    const stats = payload.stats && typeof payload.stats === 'object'
      ? payload.stats as RegimeView['stats']
      : null;
    const mlModel = payload.mlModel && typeof payload.mlModel === 'object'
      ? payload.mlModel as RegimeView['mlModel']
      : null;
    return {
      current: {
        regime,
        method: typeof current.method === 'string' ? current.method : '',
        confidence: finite(current.confidence),
        riskMultiplier: finite(current.riskMultiplier) ?? 1,
        allocation: current.allocation && typeof current.allocation === 'object'
          ? current.allocation as Record<string, number>
          : {},
        timestamp: typeof current.timestamp === 'string' ? current.timestamp : undefined,
      },
      stats,
      mlModel,
    };
  }

  const regime = typeof payload.regime === 'string' ? payload.regime : '';
  if (!regime) return null;
  const allocation = payload.allocation && typeof payload.allocation === 'object'
    ? payload.allocation as Record<string, number>
    : {};
  return {
    current: {
      regime,
      method: typeof payload.method === 'string' ? payload.method : '',
      confidence: finite(payload.confidence),
      riskMultiplier: finite(payload.riskMultiplier ?? payload.risk_multiplier) ?? 1,
      allocation,
      timestamp: typeof payload.timestamp === 'string' ? payload.timestamp : undefined,
      trend: finite(payload.trend),
      volatility: finite(payload.volatility),
      marketBreadth: finite(payload.marketBreadth),
    },
    stats: null,
    mlModel: null,
  };
}

export function RegimeDashboard() {
  const [data, setData] = useState<RegimeView | null>(null);
  const [empty, setEmpty] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    const fetchRegimeData = async () => {
      try {
        const response = await fetch('/api/bot/regime');
        if (!response.ok) throw new Error('Failed to fetch');
        const payload = await response.json();
        const view = readRegime(payload);
        if (!cancelled) {
          setData(view);
          setEmpty(view == null);
        }
      } catch (err) {
        console.error('Error fetching regime data:', err);
        if (!cancelled) setEmpty(true);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetchRegimeData();
    const interval = setInterval(fetchRegimeData, 30000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  if (loading) {
    return <div className="text-center p-8 text-gray-300">Loading regime data...</div>;
  }

  if (!data) {
    return (
      <div className="text-center p-8 text-gray-300">
        {empty ? 'No regime reading in the last 3 days.' : 'Regime reading unavailable.'}
      </div>
    );
  }

  const { current, stats, mlModel } = data;
  const label = regimeLabels[current.regime] ?? current.regime;
  const confidenceText = current.confidence == null
    ? 'Confidence not in this reading'
    : `${(current.confidence * 100).toFixed(1)}% confidence`;
  const allocationEntries = Object.entries(current.allocation || {}).filter(
    ([, value]) => Number.isFinite(Number(value))
  );

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-lg border border-slate-700 bg-slate-800 p-6">
          <div className="text-sm font-medium text-slate-400 mb-2">Current Regime</div>
          <div className="flex items-center gap-2">
            <div className={`h-3 w-3 rounded-full ${regimeColors[current.regime] ?? 'bg-gray-500'}`} />
            <div className="text-2xl font-bold text-white">{label}</div>
          </div>
          <div className="mt-2 text-xs text-slate-400">
            {current.method === 'ml' ? 'ML' : current.method || 'Rule-based'} • {confidenceText}
          </div>
        </div>

        <div className="rounded-lg border border-slate-700 bg-slate-800 p-6">
          <div className="text-sm font-medium text-slate-400 mb-2">ML Model Accuracy</div>
          <div className="text-2xl font-bold text-slate-200">
            {mlModel ? `${(mlModel.accuracy * 100).toFixed(1)}%` : 'Not measured'}
          </div>
          <div className="mt-2 text-xs text-slate-400">
            {mlModel ? 'Checked against later prices' : 'No accuracy history on this reading'}
          </div>
        </div>

        <div className="rounded-lg border border-slate-700 bg-slate-800 p-6">
          <div className="text-sm font-medium text-slate-400 mb-2">Risk Multiplier</div>
          <div className="text-2xl font-bold text-white">{current.riskMultiplier.toFixed(2)}x</div>
          <div className="mt-2 text-xs text-slate-400">
            Position sizing adjustment
          </div>
        </div>

        <div className="rounded-lg border border-slate-700 bg-slate-800 p-6">
          <div className="text-sm font-medium text-slate-400 mb-2">Regime Changes</div>
          <div className="text-2xl font-bold text-white">{stats ? stats.totalChanges : '—'}</div>
          <div className="mt-2 text-xs text-slate-400">
            {stats
              ? `Last 7 days • Avg: ${(stats.averageConfidence * 100).toFixed(1)}%`
              : 'Change history is not on this reading'}
          </div>
        </div>
      </div>

      <div className="rounded-lg border border-slate-700 bg-slate-800 p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Strategy Allocation</h3>
        {allocationEntries.length === 0 ? (
          <p className="text-sm text-slate-400">No allocation on this reading.</p>
        ) : (
          <div className="space-y-4">
            {allocationEntries.map(([strategy, allocation]) => {
              const raw = Number(allocation);
              const pct = raw <= 1 ? raw * 100 : raw;
              const width = Math.max(0, Math.min(100, pct));
              return (
                <div key={strategy}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="font-medium text-slate-200">{strategy}</span>
                    <span className="text-slate-400">{width.toFixed(0)}%</span>
                  </div>
                  <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-cyan-500 transition-all"
                      style={{ width: `${width}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {current.trend != null || current.volatility != null || current.marketBreadth != null ? (
        <div className="rounded-lg border border-slate-700 bg-slate-800 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Reading Detail</h3>
          <div className="grid gap-4 md:grid-cols-3 text-sm">
            <div>
              <div className="text-slate-400">Trend slope</div>
              <div className="text-white font-medium">{current.trend == null ? '—' : current.trend.toFixed(4)}</div>
            </div>
            <div>
              <div className="text-slate-400">Volatility</div>
              <div className="text-white font-medium">{current.volatility == null ? '—' : `${current.volatility.toFixed(2)}×`}</div>
            </div>
            <div>
              <div className="text-slate-400">Breadth</div>
              <div className="text-white font-medium">
                {current.marketBreadth == null ? '—' : `${(current.marketBreadth * 100).toFixed(1)}% above 20-day average`}
              </div>
            </div>
          </div>
        </div>
      ) : null}

      {mlModel && mlModel.features?.length ? (
        <div className="rounded-lg border border-slate-700 bg-slate-800 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">ML Feature Importance</h3>
          <div className="space-y-4">
            {mlModel.features.map((feature) => (
              <div key={feature.name}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="font-medium text-slate-200 capitalize">{feature.name.replace(/_/g, ' ')}</span>
                  <span className="text-slate-400">{(feature.importance * 100).toFixed(1)}%</span>
                </div>
                <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-500 transition-all"
                    style={{ width: `${Math.max(0, Math.min(100, feature.importance * 100))}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {stats?.regimeDistribution ? (
        <div className="rounded-lg border border-slate-700 bg-slate-800 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Regime Distribution (7 Days)</h3>
          <div className="space-y-4">
            {Object.entries(stats.regimeDistribution)
              .sort(([, a], [, b]) => b - a)
              .map(([regime, percentage]) => (
                <div key={regime}>
                  <div className="flex justify-between text-sm mb-1">
                    <div className="flex items-center gap-2">
                      <div className={`h-3 w-3 rounded-full ${regimeColors[regime] ?? 'bg-gray-500'}`} />
                      <span className="font-medium text-slate-200">{regimeLabels[regime] ?? regime}</span>
                    </div>
                    <span className="text-slate-400">{percentage}%</span>
                  </div>
                  <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${regimeColors[regime] ?? 'bg-gray-500'} transition-all`}
                      style={{ width: `${Math.max(0, Math.min(100, percentage))}%` }}
                    />
                  </div>
                </div>
              ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}
