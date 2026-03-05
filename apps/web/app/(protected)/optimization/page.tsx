'use client';

import { ProtectedRoute } from '@/components/protected-route';
import { LayoutWrapper } from '@/components/layout-wrapper';
import { useState, useEffect } from 'react';
import { TrendingUp, Activity, AlertCircle, CheckCircle, XCircle, Settings, BarChart3, Brain } from 'lucide-react';

interface OptimizationRecord {
  timestamp: string;
  strategy_name: string;
  current_params: Record<string, any>;
  optimal_params: Record<string, any>;
  train_sharpe: number;
  test_sharpe: number;
  improvement_pct: number;
  applied: boolean;
}

interface RegimeAccuracy {
  total_predictions: number;
  ml_accuracy: number;
  rule_accuracy: number;
  ml_better: boolean;
  accuracy_difference: number;
  high_confidence_accuracy: number;
}

interface StrategyStatus {
  strategy_name: string;
  enabled: boolean;
  disabled_reason?: string;
  disabled_at?: string;
  performance_metrics?: {
    win_rate: number;
    sharpe: number;
    trades: number;
  };
}

export default function OptimizationPage() {
  return (
    <ProtectedRoute>
      <LayoutWrapper>
        <OptimizationContent />
      </LayoutWrapper>
    </ProtectedRoute>
  );
}

function OptimizationContent() {
  const [optimizationHistory, setOptimizationHistory] = useState<OptimizationRecord[]>([]);
  const [regimeAccuracy, setRegimeAccuracy] = useState<RegimeAccuracy | null>(null);
  const [strategyStatus, setStrategyStatus] = useState<StrategyStatus[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOptimizationData();
    const interval = setInterval(fetchOptimizationData, 60000);
    return () => clearInterval(interval);
  }, []);

  const fetchOptimizationData = async () => {
    try {
      setLoading(true);
      
      // Fetch optimization history
      const historyRes = await fetch('/api/bot/optimization-history');
      if (historyRes.ok) {
        setOptimizationHistory(await historyRes.json());
      }

      // Fetch regime accuracy
      const accuracyRes = await fetch('/api/bot/regime-accuracy');
      if (accuracyRes.ok) {
        setRegimeAccuracy(await accuracyRes.json());
      }

      // Fetch strategy status
      const statusRes = await fetch('/api/bot/strategy-status');
      if (statusRes.ok) {
        setStrategyStatus(await statusRes.json());
      }
    } catch (error) {
      console.error('Error fetching optimization data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-slate-400">Loading optimization data...</div>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Optimization Monitoring</h1>
        <p className="text-slate-400">Track parameter optimization, regime accuracy, and strategy performance</p>
      </div>

      {/* Regime Accuracy Comparison */}
      {regimeAccuracy && (
        <div className="bg-slate-800/50 rounded-xl border border-slate-700 p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="h-10 w-10 bg-purple-600/20 rounded-lg flex items-center justify-center">
              <Brain className="h-5 w-5 text-purple-400" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-white">ML vs Rule-Based Regime Detection</h2>
              <p className="text-sm text-slate-400">Accuracy comparison over last 30 days</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-slate-900/50 rounded-lg p-4">
              <p className="text-slate-400 text-xs mb-2">ML Accuracy</p>
              <p className="text-3xl font-bold text-blue-400">{regimeAccuracy.ml_accuracy.toFixed(1)}%</p>
              <p className="text-xs text-slate-500 mt-1">{regimeAccuracy.total_predictions} predictions</p>
            </div>
            <div className="bg-slate-900/50 rounded-lg p-4">
              <p className="text-slate-400 text-xs mb-2">Rule-Based Accuracy</p>
              <p className="text-3xl font-bold text-orange-400">{regimeAccuracy.rule_accuracy.toFixed(1)}%</p>
              <p className="text-xs text-slate-500 mt-1">Traditional indicators</p>
            </div>
            <div className="bg-slate-900/50 rounded-lg p-4">
              <p className="text-slate-400 text-xs mb-2">Difference</p>
              <p className={`text-3xl font-bold ${regimeAccuracy.ml_better ? 'text-green-400' : 'text-red-400'}`}>
                {regimeAccuracy.ml_better ? '+' : ''}{regimeAccuracy.accuracy_difference.toFixed(1)}%
              </p>
              <p className="text-xs text-slate-500 mt-1">
                {regimeAccuracy.ml_better ? 'ML performing better' : 'Rule-based performing better'}
              </p>
            </div>
          </div>

          {regimeAccuracy.high_confidence_accuracy > 0 && (
            <div className="mt-4 bg-blue-900/20 border border-blue-700/50 rounded-lg p-3">
              <p className="text-sm text-blue-300">
                High confidence predictions ({'>'}80%): {regimeAccuracy.high_confidence_accuracy.toFixed(1)}% accuracy
              </p>
            </div>
          )}
        </div>
      )}

      {/* Strategy Status */}
      <div className="bg-slate-800/50 rounded-xl border border-slate-700 overflow-hidden">
        <div className="p-5 border-b border-slate-700">
          <h2 className="text-lg font-semibold text-white">Strategy Status</h2>
          <p className="text-sm text-slate-400 mt-1">Auto-enable/disable based on performance</p>
        </div>
        <div className="divide-y divide-slate-700">
          {strategyStatus.length === 0 ? (
            <div className="p-8 text-center text-slate-400">
              No strategy status data available
            </div>
          ) : (
            strategyStatus.map((strategy) => (
              <div key={strategy.strategy_name} className="p-4 hover:bg-slate-700/30 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {strategy.enabled ? (
                      <CheckCircle className="h-5 w-5 text-green-400" />
                    ) : (
                      <XCircle className="h-5 w-5 text-red-400" />
                    )}
                    <div>
                      <p className="text-white font-medium">{strategy.strategy_name}</p>
                      {strategy.disabled_reason && (
                        <p className="text-sm text-red-400 mt-1">{strategy.disabled_reason}</p>
                      )}
                    </div>
                  </div>
                  <div className="text-right">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      strategy.enabled ? 'bg-green-900/50 text-green-400' : 'bg-red-900/50 text-red-400'
                    }`}>
                      {strategy.enabled ? 'Active' : 'Disabled'}
                    </span>
                    {strategy.performance_metrics && (
                      <div className="flex items-center gap-3 mt-2 text-xs text-slate-400">
                        <span>WR: {(strategy.performance_metrics.win_rate * 100).toFixed(1)}%</span>
                        <span>Sharpe: {strategy.performance_metrics.sharpe.toFixed(2)}</span>
                        <span>{strategy.performance_metrics.trades} trades</span>
                      </div>
                    )}
                  </div>
                </div>
                {strategy.disabled_at && (
                  <p className="text-xs text-slate-500 mt-2">
                    Disabled: {new Date(strategy.disabled_at).toLocaleString()}
                  </p>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* Optimization History */}
      <div className="bg-slate-800/50 rounded-xl border border-slate-700 overflow-hidden">
        <div className="p-5 border-b border-slate-700">
          <h2 className="text-lg font-semibold text-white">Parameter Optimization History</h2>
          <p className="text-sm text-slate-400 mt-1">Recent parameter re-optimizations</p>
        </div>
        {optimizationHistory.length === 0 ? (
          <div className="p-8 text-center">
            <Settings className="mx-auto h-12 w-12 text-slate-600 mb-3" />
            <p className="text-slate-400">No optimization history yet</p>
            <p className="text-sm text-slate-500 mt-1">
              Parameter optimization runs monthly after 50+ trades
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-900/50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Date</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Strategy</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Parameters</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">Train Sharpe</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">Test Sharpe</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">Improvement</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-slate-400 uppercase tracking-wider">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/50">
                {optimizationHistory.map((record, idx) => (
                  <tr key={idx} className="hover:bg-slate-700/30 transition-colors">
                    <td className="px-4 py-3 text-sm text-slate-300">
                      {new Date(record.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                    </td>
                    <td className="px-4 py-3 text-sm font-medium text-white">{record.strategy_name}</td>
                    <td className="px-4 py-3 text-sm text-slate-300">
                      <div className="space-y-1">
                        {record.optimal_params && Object.entries(record.optimal_params).slice(0, 2).map(([key, value]) => (
                          <div key={key} className="text-xs">
                            <span className="text-slate-500">{key}:</span>{' '}
                            <span className="text-slate-300">{String(value)}</span>
                          </div>
                        ))}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-white">{record.train_sharpe.toFixed(2)}</td>
                    <td className="px-4 py-3 text-sm text-right text-white">{record.test_sharpe.toFixed(2)}</td>
                    <td className="px-4 py-3 text-sm text-right">
                      <span className={`font-medium ${record.improvement_pct >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {record.improvement_pct >= 0 ? '+' : ''}{record.improvement_pct.toFixed(1)}%
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      {record.applied ? (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-900/50 text-green-400">
                          Applied
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-900/50 text-yellow-400">
                          Pending
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Info Box */}
      <div className="bg-blue-900/20 border border-blue-700/50 rounded-xl p-4">
        <div className="flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-blue-400 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-blue-300">
            <p className="font-medium mb-1">About Optimization Monitoring</p>
            <ul className="space-y-1 text-blue-300/80">
              <li>• Parameter optimization runs automatically every 30 days (requires 50+ trades)</li>
              <li>• Strategies auto-disable if win rate {'<'} 40% or Sharpe {'<'} 0.5 for 30 days</li>
              <li>• ML regime accuracy is validated against actual market behavior</li>
              <li>• All automation features are disabled by default and require manual enablement</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
