'use client';

import { useEffect, useState } from 'react';
import { Navigation } from '@/components/navigation';
import { ReleaseBanner } from '@/components/release-banner';
import { useAuth } from '@/lib/auth-context';
import { Activity, TrendingUp, AlertTriangle, BarChart3, RefreshCw } from 'lucide-react';

interface BotHealth {
  botName: string;
  lastHeartbeat: string | null;
  heartbeatAgeSeconds: number | null;
  errors24h: number;
  currentRegime: string;
  activeStrategies: number;
  unrealizedPl: number;
  openPositions: number;
  status: string;
}

interface StrategyPerformance {
  botName: string;
  strategyName: string;
  totalTrades: number;
  winRate: number;
  totalPnl: number;
  sharpeRatio: number | null;
  profitFactor: number | null;
  openPositions: number;
  status: string;
}

interface RiskMetrics {
  portfolioHeat: number | null;
  maxPortfolioHeat: number;
  maxDrawdown: number;
  maxDrawdownLimit: number;
  dailyPnl: number;
  dailyLossLimit: number;
  openPositions: number;
  maxPositions: number;
}

interface MarketRegime {
  regime: string;
  confidence: number | null;
  trend: number | null;
  volatility: number | null;
  marketBreadth: number | null;
  vix: number | null;
}

const REGIME_PRESENTATION: Record<string, { label: string; badge: string }> = {
  BULL_TRENDING: { label: 'Bull Trending', badge: 'bg-green-500/20 text-green-400 border-green-500/50' },
  BEAR_TRENDING: { label: 'Bear Trending', badge: 'bg-red-500/20 text-red-400 border-red-500/50' },
  HIGH_VOL_CHOPPY: { label: 'High Vol Choppy', badge: 'bg-orange-500/20 text-orange-400 border-orange-500/50' },
  LOW_VOL_RANGE: { label: 'Low Vol Range', badge: 'bg-blue-500/20 text-blue-400 border-blue-500/50' },
  CRISIS: { label: 'Crisis', badge: 'bg-purple-500/20 text-purple-400 border-purple-500/50' },
};

function regimePresentation(regime: string | null | undefined) {
  const key = (regime || '').trim().toUpperCase();
  return REGIME_PRESENTATION[key] || {
    label: key ? key.split('_').join(' ') : 'Unknown',
    badge: 'bg-slate-500/20 text-slate-400 border-slate-500/50',
  };
}

function botLabel(name: string) {
  if (name.includes('equity')) return 'Equity';
  if (name.includes('crypto')) return 'Crypto';
  if (name.includes('kraken')) return 'Kraken';
  return name;
}

function formatAge(seconds: number | null) {
  if (seconds == null) return 'N/A';
  if (seconds < 90) return 'just now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  return `${Math.floor(minutes / 60)}h ${minutes % 60}m ago`;
}

function formatWinRate(value: number | null | undefined) {
  if (value == null || Number.isNaN(value)) return 'N/A';
  return `${value.toFixed(1)}%`;
}

function statusLabel(status: string) {
  const normalized = (status || '').toLowerCase();
  if (normalized === 'running') return 'Running';
  if (normalized === 'stale') return 'Stale';
  return status || 'Unknown';
}

function meterColor(ratio: number) {
  if (ratio > 0.8) return 'bg-red-500';
  if (ratio > 0.6) return 'bg-yellow-500';
  return 'bg-green-500';
}

function Meter({ ratio }: { ratio: number | null }) {
  const raw = ratio != null && Number.isFinite(ratio) ? ratio : 0;
  const width = Math.max(0, Math.min(raw, 1)) * 100;
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-slate-700">
      <div className={`h-2 rounded-full ${meterColor(raw)}`} style={{ width: `${width}%` }} />
    </div>
  );
}

export default function MonitoringPage() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [botHealth, setBotHealth] = useState<BotHealth[]>([]);
  const [strategyPerformance, setStrategyPerformance] = useState<StrategyPerformance[]>([]);
  const [riskMetrics, setRiskMetrics] = useState<RiskMetrics | null>(null);
  const [marketRegime, setMarketRegime] = useState<MarketRegime | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  const fetchData = async () => {
    try {
      const [healthRes, strategyRes, riskRes, regimeRes] = await Promise.all([
        fetch('/api/bot/health'),
        fetch('/api/bot/strategy-performance'),
        fetch('/api/bot/risk-metrics'),
        fetch('/api/bot/regime'),
      ]);

      if (healthRes.ok) {
        const data = await healthRes.json();
        setBotHealth(data.bots || []);
      }

      if (strategyRes.ok) {
        const data = await strategyRes.json();
        setStrategyPerformance(data.strategies || []);
      }

      if (riskRes.ok) {
        const data = await riskRes.json();
        setRiskMetrics(data);
      }

      if (regimeRes.ok) {
        const data = await regimeRes.json();
        setMarketRegime(data);
      }

      setLastUpdate(new Date());
    } catch (error) {
      console.error('Failed to fetch monitoring data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 15000); // Refresh every 15 seconds
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: string) => {
    if (!status) return 'text-gray-400';
    switch (status.toLowerCase()) {
      case 'active':
      case 'running':
        return 'text-green-400';
      case 'standby':
      case 'stale':
        return 'text-yellow-400';
      case 'error':
      case 'stopped':
        return 'text-red-400';
      default:
        return 'text-gray-400';
    }
  };

  const formatCurrency = (value: number | null | undefined) => {
    if (value == null || isNaN(value)) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value);
  };

  const formatPercent = (value: number | null | undefined) => {
    if (value == null || isNaN(value)) return 'N/A';
    return `${(value * 100).toFixed(1)}%`;
  };

  if (loading) {
    return (
      <div className="flex h-screen bg-slate-900">
        <Navigation />
        <main className="flex-1 lg:ml-64 overflow-y-auto">
          {user && <ReleaseBanner userId={user.id} />}
          <div className="p-8">
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500" />
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-slate-900">
      <Navigation />
      <main className="flex-1 lg:ml-64 overflow-y-auto">
        {user && <ReleaseBanner userId={user.id} />}
        <div className="p-8">
          <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-white">Real-Time Monitoring</h1>
                <p className="text-slate-400 mt-1">Live system health and performance metrics</p>
              </div>
              <div className="flex items-center gap-4">
                <div className="text-sm text-slate-400">
                  Last updated: {lastUpdate.toLocaleTimeString()}
                </div>
                <button
                  onClick={fetchData}
                  className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
                  title="Refresh data"
                >
                  <RefreshCw className="h-5 w-5 text-slate-400" />
                </button>
              </div>
            </div>

            {/* Bot Health Section */}
            <div>
              <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                <Activity className="h-5 w-5 text-cyan-400" />
                Bot Health
              </h2>
              {botHealth.length === 0 ? (
                <p className="text-sm text-slate-400">No bot heartbeats are available.</p>
              ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {botHealth.map((bot) => {
                  const regime = regimePresentation(bot.currentRegime);
                  return (
                  <div key={bot.botName} className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-white">{botLabel(bot.botName)}</h3>
                      <span className={`text-sm font-medium ${getStatusColor(bot.status)}`}>
                        {statusLabel(bot.status)}
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-xs text-slate-400">Last seen</p>
                        <p className="text-sm font-medium text-white">{formatAge(bot.heartbeatAgeSeconds)}</p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-400">Errors (24h)</p>
                        <p className={`text-sm font-medium ${bot.errors24h > 0 ? 'text-red-400' : 'text-green-400'}`}>
                          {bot.errors24h}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-400">Open positions</p>
                        <p className="text-sm font-medium text-white">{bot.openPositions}</p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-400">Strategies this week</p>
                        <p className="text-sm font-medium text-white">{bot.activeStrategies}</p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-400">Unrealized P&L</p>
                        <p className={`text-sm font-medium ${bot.unrealizedPl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {formatCurrency(bot.unrealizedPl)}
                        </p>
                      </div>
                    </div>
                    <div className="mt-4 pt-4 border-t border-slate-700">
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-slate-400">Current Regime</span>
                        <span className={`px-2 py-1 rounded text-xs font-medium border ${regime.badge}`}>
                          {regime.label}
                        </span>
                      </div>
                    </div>
                  </div>
                  );
                })}
              </div>
              )}
            </div>

            {/* Strategy Performance Section */}
            <div>
              <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-green-400" />
                Strategy Performance
              </h2>
              <div className="bg-slate-800/50 rounded-xl border border-slate-700 overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-slate-900/50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Strategy</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Bot</th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">Trades</th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">Win Rate</th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">All Time</th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">Profit Factor</th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">Sharpe</th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">Positions</th>
                        <th className="px-6 py-3 text-center text-xs font-medium text-slate-400 uppercase tracking-wider">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-700">
                      {strategyPerformance.length === 0 ? (
                        <tr>
                          <td colSpan={9} className="px-6 py-4 text-sm text-slate-400">No closed-trade results yet.</td>
                        </tr>
                      ) : strategyPerformance.map((strategy) => (
                        <tr key={`${strategy.botName}-${strategy.strategyName}`} className="hover:bg-slate-700/30">
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">
                            {strategy.strategyName}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-300">
                            {botLabel(strategy.botName)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-white">
                            {strategy.totalTrades}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-white">
                            {formatWinRate(strategy.winRate)}
                          </td>
                          <td className={`px-6 py-4 whitespace-nowrap text-sm text-right ${strategy.totalPnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                            {formatCurrency(strategy.totalPnl)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-white">
                            {strategy.profitFactor != null ? strategy.profitFactor.toFixed(2) : 'N/A'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-slate-300">
                            {strategy.sharpeRatio != null ? strategy.sharpeRatio.toFixed(2) : 'N/A'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-white">
                            {strategy.openPositions}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-center">
                            <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(strategy.status)}`}>
                              {statusLabel(strategy.status)}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* Risk Metrics Section */}
            {riskMetrics && (
              <div>
                <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-yellow-400" />
                  Risk Metrics
                  <span className="text-sm font-normal text-slate-400">Equity</span>
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="min-w-0 overflow-hidden bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-sm text-slate-400">Portfolio Heat</p>
                      <p className="text-xs text-slate-500">{formatPercent(riskMetrics.maxPortfolioHeat)} max</p>
                    </div>
                    <div className="mb-2">
                      <p className="text-2xl font-bold text-white">
                        {riskMetrics.portfolioHeat == null ? 'N/A' : formatPercent(riskMetrics.portfolioHeat)}
                      </p>
                    </div>
                    <Meter ratio={riskMetrics.portfolioHeat == null || riskMetrics.maxPortfolioHeat <= 0 ? null : riskMetrics.portfolioHeat / riskMetrics.maxPortfolioHeat} />
                    {riskMetrics.portfolioHeat == null && (
                      <p className="mt-2 text-xs text-slate-500">Stops are not stored on the open positions</p>
                    )}
                  </div>

                  <div className="min-w-0 overflow-hidden bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-sm text-slate-400">Max Drawdown</p>
                      <p className="text-xs text-slate-500">{formatPercent(riskMetrics.maxDrawdownLimit)} limit</p>
                    </div>
                    <div className="mb-2">
                      <p className="text-2xl font-bold text-white">{formatPercent(riskMetrics.maxDrawdown)}</p>
                    </div>
                    <Meter ratio={riskMetrics.maxDrawdownLimit > 0 ? riskMetrics.maxDrawdown / riskMetrics.maxDrawdownLimit : null} />
                  </div>

                  <div className="min-w-0 overflow-hidden bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-sm text-slate-400">Daily P&L</p>
                      <p className="text-xs text-slate-500">{formatCurrency(riskMetrics.dailyLossLimit)} limit</p>
                    </div>
                    <div className="mb-2">
                      <p className={`text-2xl font-bold ${riskMetrics.dailyPnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {formatCurrency(riskMetrics.dailyPnl)}
                      </p>
                    </div>
                    <Meter ratio={riskMetrics.dailyLossLimit > 0 ? Math.abs(riskMetrics.dailyPnl) / riskMetrics.dailyLossLimit : null} />
                  </div>

                  <div className="min-w-0 overflow-hidden bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-sm text-slate-400">Open Positions</p>
                      <p className="text-xs text-slate-500">{riskMetrics.maxPositions} max</p>
                    </div>
                    <div className="mb-2">
                      <p className="text-2xl font-bold text-white">{riskMetrics.openPositions}</p>
                    </div>
                    <Meter ratio={riskMetrics.maxPositions > 0 ? riskMetrics.openPositions / riskMetrics.maxPositions : null} />
                  </div>
                </div>
              </div>
            )}

            {/* Market Regime Section */}
            {marketRegime && (
              <div>
                <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                  <BarChart3 className="h-5 w-5 text-purple-400" />
                  Market Regime
                  <span className="text-sm font-normal text-slate-400">Equity</span>
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                    <p className="text-sm text-slate-400 mb-2">Current Regime</p>
                    <div className="flex items-center justify-between">
                      <span className={`px-3 py-2 rounded-lg text-lg font-semibold border ${regimePresentation(marketRegime.regime).badge}`}>
                        {regimePresentation(marketRegime.regime).label}
                      </span>
                      <div className="text-right">
                        <p className="text-xs text-slate-400">Confidence</p>
                        <p className="text-lg font-bold text-white">{formatPercent(marketRegime.confidence)}</p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                    <p className="text-sm text-slate-400 mb-2">Trend</p>
                    <p className="text-2xl font-bold text-white">
                      {marketRegime.trend == null ? 'N/A' : marketRegime.trend > 0.001 ? 'Rising' : marketRegime.trend < -0.001 ? 'Falling' : 'Flat'}
                    </p>
                    <p className="text-xs text-slate-500 mt-1">
                      {marketRegime.trend == null ? '50-day average slope' : `${marketRegime.trend.toFixed(4)} slope of the 50-day average`}
                    </p>
                  </div>

                  <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                    <p className="text-sm text-slate-400 mb-2">Volatility</p>
                    <p className="text-2xl font-bold text-white">{marketRegime.volatility != null ? `${marketRegime.volatility.toFixed(2)}×` : 'N/A'}</p>
                    <p className="text-xs text-slate-500 mt-1">ATR compared with its average</p>
                  </div>

                  <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                    <p className="text-sm text-slate-400 mb-2">Market Breadth</p>
                    <p className="text-2xl font-bold text-white">{formatPercent(marketRegime.marketBreadth)}</p>
                    <p className="text-xs text-slate-500 mt-1">Share above their 20-day average</p>
                  </div>

                  <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                    <p className="text-sm text-slate-400 mb-2">VIX Level</p>
                    <p className={`text-2xl font-bold ${marketRegime.vix == null ? 'text-slate-400' : marketRegime.vix > 30 ? 'text-red-400' : marketRegime.vix > 20 ? 'text-yellow-400' : 'text-green-400'}`}>
                      {marketRegime.vix != null ? marketRegime.vix.toFixed(2) : 'N/A'}
                    </p>
                    <p className="text-xs text-slate-500 mt-1">
                      {marketRegime.vix == null ? 'Not in the latest reading' : 'Fear index'}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
