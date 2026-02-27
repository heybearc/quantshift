'use client';

import { useState, useEffect } from 'react';
import { Navigation } from '@/components/navigation';
import { ReleaseBanner } from '@/components/release-banner';
import { useAuth } from '@/lib/auth-context';
import { useRouter } from 'next/navigation';
import { BarChart3, TrendingUp, TrendingDown, Target, Award, AlertTriangle, BarChart2, Bitcoin } from 'lucide-react';
import Link from 'next/link';

type BotFilter = 'all' | 'equity-bot' | 'crypto-bot';

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

interface StrategyPerformance {
  strategyName: string;
  totalTrades: number;
  winningTrades: number;
  losingTrades: number;
  winRate: number;
  totalPnl: number;
  totalPnlPct: number;
  sharpeRatio?: number;
  profitFactor?: number;
  maxDrawdown?: number;
}

export default function PerformancePage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [performance, setPerformance] = useState<PerformanceData | null>(null);
  const [strategyPerformance, setStrategyPerformance] = useState<StrategyPerformance[]>([]);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('30');
  const [botFilter, setBotFilter] = useState<BotFilter>('all');

  useEffect(() => {
    if (!authLoading && !user) router.push('/login');
  }, [user, authLoading, router]);

  useEffect(() => {
    if (user) {
      fetchPerformance();
      fetchStrategyPerformance();
    }
  }, [user, timeRange, botFilter]);

  const fetchPerformance = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({ days: timeRange });
      if (botFilter !== 'all') params.set('botName', botFilter);
      const response = await fetch(`/api/bot/performance?${params}`);
      if (response.ok) setPerformance(await response.json());
    } catch (error) {
      console.error('Error fetching performance:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStrategyPerformance = async () => {
    try {
      const params = new URLSearchParams();
      if (botFilter !== 'all') params.set('botName', botFilter);
      const response = await fetch(`/api/bot/strategy-performance?${params}`);
      if (response.ok) {
        const data = await response.json();
        setStrategyPerformance(data.strategies || []);
      }
    } catch (error) {
      console.error('Error fetching strategy performance:', error);
    }
  };

  const fmt = (v: number) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(v);
  const fmtPct = (v: number) => `${v >= 0 ? '+' : ''}${fmt2(v)}%`;

  if (authLoading) return (
    <div className="min-h-screen flex items-center justify-center bg-slate-900">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500" />
    </div>
  );
  if (!user) return null;

  const summary = performance?.summary;
  const strategyLabel = botFilter === 'equity-bot'
    ? 'MA Crossover · 5/20 Daily SMA'
    : botFilter === 'crypto-bot'
    ? 'MA/RSI/MACD · 20/50 Hourly SMA'
    : 'All Strategies Combined';

  return (
    <div className="flex h-screen bg-slate-900">
      <Navigation />
      <main className="flex-1 lg:ml-64 overflow-y-auto">
        {user && <ReleaseBanner userId={user.id} />}
        <div className="p-8">
          <div className="space-y-6">

            {/* Header */}
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <h1 className="text-3xl font-bold text-white">Performance</h1>
                <p className="text-slate-400 mt-1">Trading performance over the last {timeRange} days</p>
              </div>
              <div className="flex items-center gap-3">
                <select
                  value={timeRange}
                  onChange={(e) => setTimeRange(e.target.value)}
                  className="px-3 py-2 bg-slate-800 border border-slate-700 text-white text-sm rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500"
                >
                  <option value="7">Last 7 days</option>
                  <option value="30">Last 30 days</option>
                  <option value="90">Last 90 days</option>
                  <option value="365">Last year</option>
                </select>
                <Link href="/dashboard" className="px-3 py-2 text-sm font-medium text-slate-400 hover:text-white bg-slate-800 border border-slate-700 rounded-lg transition-colors">
                  ← Dashboard
                </Link>
              </div>
            </div>

            {/* Bot filter tabs */}
            <div className="flex items-center gap-1 bg-slate-800/50 rounded-xl p-1 border border-slate-700 w-fit">
              {([
                { id: 'all' as BotFilter, label: 'All Bots', icon: null },
                { id: 'equity-bot' as BotFilter, label: 'Equity Bot', icon: <BarChart2 className="h-3.5 w-3.5" /> },
                { id: 'crypto-bot' as BotFilter, label: 'Crypto Bot', icon: <Bitcoin className="h-3.5 w-3.5" /> },
              ]).map(({ id, label, icon }) => (
                <button key={id} onClick={() => setBotFilter(id)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    botFilter === id ? 'bg-cyan-600 text-white shadow' : 'text-slate-400 hover:text-white hover:bg-slate-700'
                  }`}>
                  {icon}{label}
                </button>
              ))}
            </div>

            {loading ? (
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500" />
              </div>
            ) : !summary || summary.totalTrades === 0 ? (
              <div className="bg-slate-800/50 rounded-xl border border-slate-700 p-16 text-center">
                <AlertTriangle className="mx-auto h-12 w-12 text-slate-600 mb-4" />
                <h3 className="text-lg font-medium text-white mb-2">No Performance Data Yet</h3>
                <p className="text-slate-400">Metrics will populate once trades are closed.</p>
              </div>
            ) : (
              <>
                {/* Key metrics */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-slate-800/50 rounded-xl p-5 border border-slate-700">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-slate-400 text-xs font-medium">Total P&L</p>
                      {summary.totalPnl >= 0 ? <TrendingUp className="h-4 w-4 text-green-400" /> : <TrendingDown className="h-4 w-4 text-red-400" />}
                    </div>
                    <p className={`text-2xl font-bold ${summary.totalPnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>{fmt(summary.totalPnl)}</p>
                    <p className={`text-xs mt-1 ${summary.totalPnlPct >= 0 ? 'text-green-400' : 'text-red-400'}`}>{fmtPct(summary.totalPnlPct)}</p>
                  </div>
                  <div className="bg-slate-800/50 rounded-xl p-5 border border-slate-700">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-slate-400 text-xs font-medium">Win Rate</p>
                      <Target className="h-4 w-4 text-blue-400" />
                    </div>
                    <p className="text-2xl font-bold text-white">{(summary.winRate || 0).toFixed(1)}%</p>
                    <p className="text-xs text-slate-500 mt-1">{summary.winningTrades}W / {summary.losingTrades}L</p>
                  </div>
                  <div className="bg-slate-800/50 rounded-xl p-5 border border-slate-700">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-slate-400 text-xs font-medium">Profit Factor</p>
                      <Award className="h-4 w-4 text-purple-400" />
                    </div>
                    <p className="text-2xl font-bold text-white">{(summary.profitFactor || 0).toFixed(2)}</p>
                    <p className="text-xs text-slate-500 mt-1">{(summary.profitFactor || 0) >= 1.5 ? 'Excellent' : (summary.profitFactor || 0) >= 1.0 ? 'Good' : 'Poor'}</p>
                  </div>
                  <div className="bg-slate-800/50 rounded-xl p-5 border border-slate-700">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-slate-400 text-xs font-medium">Sharpe Ratio</p>
                      <BarChart3 className="h-4 w-4 text-orange-400" />
                    </div>
                    <p className="text-2xl font-bold text-white">{(summary.sharpeRatio || 0).toFixed(2)}</p>
                    <p className="text-xs text-slate-500 mt-1">Risk-adjusted return</p>
                  </div>
                </div>

                {/* Secondary metrics */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-slate-800/50 rounded-xl p-5 border border-slate-700">
                    <p className="text-slate-400 text-xs font-medium mb-3">Total Trades</p>
                    <p className="text-3xl font-bold text-white mb-2">{summary.totalTrades}</p>
                    <div className="flex items-center gap-4 text-xs">
                      <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-green-500 inline-block" /><span className="text-slate-400">{summary.winningTrades} wins</span></span>
                      <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500 inline-block" /><span className="text-slate-400">{summary.losingTrades} losses</span></span>
                    </div>
                  </div>
                  <div className="bg-slate-800/50 rounded-xl p-5 border border-slate-700">
                    <p className="text-slate-400 text-xs font-medium mb-3">Max Drawdown</p>
                    <p className="text-3xl font-bold text-red-400 mb-2">{fmtPct(summary.maxDrawdown)}</p>
                    <p className="text-xs text-slate-500">Largest peak-to-trough decline</p>
                  </div>
                  <div className="bg-slate-800/50 rounded-xl p-5 border border-slate-700">
                    <p className="text-slate-400 text-xs font-medium mb-3">Strategy</p>
                    <p className="text-sm font-semibold text-white mb-1">{strategyLabel}</p>
                    <p className="text-xs text-slate-500">{botFilter === 'all' ? 'Equity + Crypto combined' : botFilter === 'equity-bot' ? 'Alpaca paper trading' : 'Coinbase dry-run'}</p>
                  </div>
                </div>

                {/* Strategy Performance Breakdown */}
                {strategyPerformance.length > 0 && (
                  <div className="bg-slate-800/50 rounded-xl border border-slate-700 overflow-hidden">
                    <div className="p-5 border-b border-slate-700">
                      <h3 className="text-sm font-semibold text-white">Strategy Performance Breakdown</h3>
                      <p className="text-xs text-slate-400 mt-1">Performance metrics by trading strategy</p>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead className="bg-slate-900/50">
                          <tr>
                            <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Strategy</th>
                            <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">Trades</th>
                            <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">Win Rate</th>
                            <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">Total P&L</th>
                            <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">Profit Factor</th>
                            <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">Sharpe</th>
                            <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">Max DD</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-700/50">
                          {strategyPerformance.map((strategy) => (
                            <tr key={strategy.strategyName} className="hover:bg-slate-700/30 transition-colors">
                              <td className="px-4 py-3 text-sm font-medium text-white">{strategy.strategyName}</td>
                              <td className="px-4 py-3 text-sm text-right text-slate-300">
                                {strategy.totalTrades}
                                <span className="block text-xs text-slate-500">{strategy.winningTrades}W / {strategy.losingTrades}L</span>
                              </td>
                              <td className="px-4 py-3 text-sm text-right text-white">{strategy.winRate.toFixed(1)}%</td>
                              <td className="px-4 py-3 text-sm text-right">
                                <span className={`font-medium ${strategy.totalPnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>{fmt(strategy.totalPnl)}</span>
                                <span className={`block text-xs ${strategy.totalPnlPct >= 0 ? 'text-green-500' : 'text-red-500'}`}>{fmtPct(strategy.totalPnlPct)}</span>
                              </td>
                              <td className="px-4 py-3 text-sm text-right text-slate-300">{strategy.profitFactor?.toFixed(2) || '—'}</td>
                              <td className="px-4 py-3 text-sm text-right text-slate-300">{strategy.sharpeRatio?.toFixed(2) || '—'}</td>
                              <td className="px-4 py-3 text-sm text-right text-red-400">{strategy.maxDrawdown ? fmtPct(strategy.maxDrawdown) : '—'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Daily table */}
                {performance!.daily.length > 0 && (
                  <div className="bg-slate-800/50 rounded-xl border border-slate-700 overflow-hidden">
                    <div className="p-5 border-b border-slate-700">
                      <h3 className="text-sm font-semibold text-white">Daily Breakdown</h3>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead className="bg-slate-900/50">
                          <tr>
                            <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Date</th>
                            <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">Trades</th>
                            <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">Win Rate</th>
                            <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">P&L</th>
                            <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">Profit Factor</th>
                            <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">Sharpe</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-700/50">
                          {performance!.daily.map((day) => (
                            <tr key={day.date} className="hover:bg-slate-700/30 transition-colors">
                              <td className="px-4 py-3 text-sm text-slate-300">{new Date(day.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</td>
                              <td className="px-4 py-3 text-sm text-right text-white">{day.totalTrades}</td>
                              <td className="px-4 py-3 text-sm text-right text-white">{day.winRate.toFixed(1)}%</td>
                              <td className="px-4 py-3 text-sm text-right">
                                <span className={`font-medium ${day.totalPnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>{fmt(day.totalPnl)}</span>
                                <span className={`block text-xs ${day.totalPnlPct >= 0 ? 'text-green-500' : 'text-red-500'}`}>{fmtPct(day.totalPnlPct)}</span>
                              </td>
                              <td className="px-4 py-3 text-sm text-right text-slate-300">{day.profitFactor?.toFixed(2) || '—'}</td>
                              <td className="px-4 py-3 text-sm text-right text-slate-300">{day.sharpeRatio?.toFixed(2) || '—'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
