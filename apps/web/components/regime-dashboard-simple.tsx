'use client';

import { useEffect, useState } from 'react';

interface RegimeData {
  current: {
    regime: string;
    method: string;
    confidence: number;
    riskMultiplier: number;
    allocation: Record<string, number>;
    timestamp: string;
  };
  stats: {
    totalChanges: number;
    averageConfidence: number;
    regimeDistribution: Record<string, number>;
  };
  mlModel: {
    accuracy: number;
    trainDate: string;
    features: Array<{
      name: string;
      importance: number;
    }>;
  };
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

export function RegimeDashboard() {
  const [data, setData] = useState<RegimeData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRegimeData();
    const interval = setInterval(fetchRegimeData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchRegimeData = async () => {
    try {
      const response = await fetch('/api/bot/regime');
      if (!response.ok) throw new Error('Failed to fetch');
      const regimeData = await response.json();
      setData(regimeData);
    } catch (err) {
      console.error('Error fetching regime data:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !data) {
    return <div className="text-center p-8 text-gray-300">Loading regime data...</div>;
  }

  const { current, stats, mlModel } = data;

  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {/* Current Regime */}
        <div className="rounded-lg border border-slate-700 bg-slate-800 p-6">
          <div className="text-sm font-medium text-slate-400 mb-2">Current Regime</div>
          <div className="flex items-center gap-2">
            <div className={`h-3 w-3 rounded-full ${regimeColors[current.regime]}`} />
            <div className="text-2xl font-bold text-white">{regimeLabels[current.regime]}</div>
          </div>
          <div className="mt-2 text-xs text-slate-400">
            {current.method === 'ml' ? '🤖 ML' : 'Rule-Based'} • {(current.confidence * 100).toFixed(1)}% confidence
          </div>
        </div>

        {/* ML Accuracy */}
        <div className="rounded-lg border border-slate-700 bg-slate-800 p-6">
          <div className="text-sm font-medium text-slate-400 mb-2">ML Model Accuracy</div>
          <div className="text-2xl font-bold text-green-400">
            {(mlModel.accuracy * 100).toFixed(1)}%
          </div>
          <div className="mt-2 text-xs text-slate-400">
            Test accuracy on 2 years
          </div>
        </div>

        {/* Risk Multiplier */}
        <div className="rounded-lg border border-slate-700 bg-slate-800 p-6">
          <div className="text-sm font-medium text-slate-400 mb-2">Risk Multiplier</div>
          <div className="text-2xl font-bold text-white">{current.riskMultiplier.toFixed(2)}x</div>
          <div className="mt-2 text-xs text-slate-400">
            Position sizing adjustment
          </div>
        </div>

        {/* Regime Changes */}
        <div className="rounded-lg border border-slate-700 bg-slate-800 p-6">
          <div className="text-sm font-medium text-slate-400 mb-2">Regime Changes</div>
          <div className="text-2xl font-bold text-white">{stats.totalChanges}</div>
          <div className="mt-2 text-xs text-slate-400">
            Last 7 days • Avg: {(stats.averageConfidence * 100).toFixed(1)}%
          </div>
        </div>
      </div>

      {/* Strategy Allocation */}
      <div className="rounded-lg border border-slate-700 bg-slate-800 p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Strategy Allocation</h3>
        <div className="space-y-4">
          {Object.entries(current.allocation).map(([strategy, allocation]) => (
            <div key={strategy}>
              <div className="flex justify-between text-sm mb-1">
                <span className="font-medium text-slate-200">{strategy}</span>
                <span className="text-slate-400">{(allocation * 100).toFixed(0)}%</span>
              </div>
              <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-cyan-500 transition-all"
                  style={{ width: `${allocation * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ML Features */}
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
                  style={{ width: `${feature.importance * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Regime Distribution */}
      <div className="rounded-lg border border-slate-700 bg-slate-800 p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Regime Distribution (7 Days)</h3>
        <div className="space-y-4">
          {Object.entries(stats.regimeDistribution)
            .sort(([, a], [, b]) => b - a)
            .map(([regime, percentage]) => (
              <div key={regime}>
                <div className="flex justify-between text-sm mb-1">
                  <div className="flex items-center gap-2">
                    <div className={`h-3 w-3 rounded-full ${regimeColors[regime]}`} />
                    <span className="font-medium text-slate-200">{regimeLabels[regime]}</span>
                  </div>
                  <span className="text-slate-400">{percentage}%</span>
                </div>
                <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${regimeColors[regime]} transition-all`}
                    style={{ width: `${percentage}%` }}
                  />
                </div>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
}
