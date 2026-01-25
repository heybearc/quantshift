'use client';

import { ProtectedRoute } from '@/components/protected-route';
import { LayoutWrapper } from '@/components/layout-wrapper';
import { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, TrendingDown, Target, Award, AlertTriangle } from 'lucide-react';
import Link from 'next/link';


// Null-safe number formatter
const fmt2 = (v: unknown) => {
  const n = typeof v === "number" ? v : Number(v);
  return Number.isFinite(n) ? n.toFixed(2) : "—";
};
interface PerformanceSummary {
  totalTrades: number;
  winningTrades: number;
  losingTrades: number;
  winRate: number;
  profitFactor: number;
  sharpeRatio: number;
  maxDrawdown: number;
  totalPnl: number;
  totalPnlPct: number;
}

interface DailyMetric {
  date: string;
  totalTrades: number;
  winningTrades: number;
  losingTrades: number;
  winRate: number;
  profitFactor?: number;
  sharpeRatio?: number;
  maxDrawdown?: number;
  totalPnl: number;
  totalPnlPct: number;
}

interface PerformanceData {
  summary: PerformanceSummary;
  daily: DailyMetric[];
}

export default function PerformancePage() {
  const [performance, setPerformance] = useState<PerformanceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('30');

  useEffect(() => {
    fetchPerformance();
  }, [timeRange]);

  const fetchPerformance = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/bot/performance?days=${timeRange}`);
      if (response.ok) {
        const data = await response.json();
        setPerformance(data);
      }
    } catch (error) {
      console.error('Error fetching performance:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${fmt2(value)}%`;
  };

  if (loading) {
    return (
      <ProtectedRoute>
        <LayoutWrapper>
        <div className="min-h-screen flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
        </LayoutWrapper>
      </ProtectedRoute>
    );
  }

  if (!performance) {
    return (
      <ProtectedRoute>
        <LayoutWrapper>
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <AlertTriangle className="mx-auto h-12 w-12 text-yellow-600 mb-4" />
            <h3 className="text-lg font-medium text-gray-900">No Performance Data</h3>
            <p className="text-gray-600 mt-2">Performance metrics will appear once the bot starts trading.</p>
          </div>
        </div>
        </LayoutWrapper>
      </ProtectedRoute>
    );
  }

  const { summary } = performance;

  return (
    <ProtectedRoute>
      <LayoutWrapper>
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Header */}
          <div className="mb-6">
            <div className="flex justify-between items-center mb-4">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Performance Metrics</h1>
                <p className="mt-1 text-gray-600">
                  Trading performance over the last {timeRange} days
                </p>
              </div>
              <div className="flex items-center gap-4">
                <select
                  value={timeRange}
                  onChange={(e) => setTimeRange(e.target.value)}
                  className="px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="7">Last 7 days</option>
                  <option value="30">Last 30 days</option>
                  <option value="90">Last 90 days</option>
                  <option value="365">Last year</option>
                </select>
                <Link
                  href="/dashboard"
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  ← Back to Dashboard
                </Link>
              </div>
            </div>
          </div>

          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {/* Total P&L */}
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-medium text-gray-600">Total P&L</h3>
                {summary.totalPnl >= 0 ? (
                  <TrendingUp className="h-5 w-5 text-green-600" />
                ) : (
                  <TrendingDown className="h-5 w-5 text-red-600" />
                )}
              </div>
              <p className={`text-2xl font-bold ${summary.totalPnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {formatCurrency(summary.totalPnl)}
              </p>
              <p className={`text-sm mt-1 ${summary.totalPnlPct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {formatPercent(summary.totalPnlPct)}
              </p>
            </div>

            {/* Win Rate */}
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-medium text-gray-600">Win Rate</h3>
                <Target className="h-5 w-5 text-blue-600" />
              </div>
              <p className="text-2xl font-bold text-gray-900">
                {(summary.winRate || 0).toFixed(1)}%
              </p>
              <p className="text-sm text-gray-600 mt-1">
                {summary.winningTrades}W / {summary.losingTrades}L
              </p>
            </div>

            {/* Profit Factor */}
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-medium text-gray-600">Profit Factor</h3>
                <Award className="h-5 w-5 text-purple-600" />
              </div>
              <p className="text-2xl font-bold text-gray-900">
                {(summary.profitFactor || 0).toFixed(2)}
              </p>
              <p className="text-sm text-gray-600 mt-1">
                {(summary.profitFactor || 0) >= 1.5 ? 'Excellent' : (summary.profitFactor || 0) >= 1.0 ? 'Good' : 'Poor'}
              </p>
            </div>

            {/* Sharpe Ratio */}
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-medium text-gray-600">Sharpe Ratio</h3>
                <BarChart3 className="h-5 w-5 text-orange-600" />
              </div>
              <p className="text-2xl font-bold text-gray-900">
                {(summary.sharpeRatio || 0).toFixed(2)}
              </p>
              <p className="text-sm text-gray-600 mt-1">
                Risk-adjusted return
              </p>
            </div>
          </div>

          {/* Additional Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            {/* Total Trades */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-sm font-medium text-gray-600 mb-4">Total Trades</h3>
              <p className="text-3xl font-bold text-gray-900 mb-2">{summary.totalTrades}</p>
              <div className="flex items-center gap-4 text-sm">
                <div className="flex items-center gap-1">
                  <div className="w-3 h-3 rounded-full bg-green-500"></div>
                  <span className="text-gray-600">{summary.winningTrades} wins</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-3 h-3 rounded-full bg-red-500"></div>
                  <span className="text-gray-600">{summary.losingTrades} losses</span>
                </div>
              </div>
            </div>

            {/* Max Drawdown */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-sm font-medium text-gray-600 mb-4">Max Drawdown</h3>
              <p className="text-3xl font-bold text-red-600 mb-2">
                {formatPercent(summary.maxDrawdown)}
              </p>
              <p className="text-sm text-gray-600">Largest peak-to-trough decline</p>
            </div>

            {/* Strategy Info */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-sm font-medium text-gray-600 mb-4">Strategy</h3>
              <p className="text-lg font-semibold text-gray-900 mb-2">MA Crossover</p>
              <p className="text-sm text-gray-600">5/20 period moving averages</p>
            </div>
          </div>

          {/* Daily Performance Table */}
          {performance.daily.length > 0 && (
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="p-6 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">Daily Performance</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Date
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Trades
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Win Rate
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        P&L
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Profit Factor
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Sharpe
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {performance.daily.map((day) => (
                      <tr key={day.date} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {new Date(day.date).toLocaleDateString('en-US', {
                            month: 'short',
                            day: 'numeric',
                            year: 'numeric',
                          })}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {day.totalTrades}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {day.winRate.toFixed(1)}%
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className={`text-sm font-medium ${day.totalPnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {formatCurrency(day.totalPnl)}
                          </div>
                          <div className={`text-xs ${day.totalPnlPct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {formatPercent(day.totalPnlPct)}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {day.profitFactor?.toFixed(2) || '—'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {day.sharpeRatio?.toFixed(2) || '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
      </LayoutWrapper>
    </ProtectedRoute>
  );
}
