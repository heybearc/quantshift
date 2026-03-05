'use client';

import { useEffect, useState } from 'react';
import { Navigation } from '@/components/navigation';
import { ReleaseBanner } from '@/components/release-banner';
import { useAuth } from '@/lib/auth-context';
import { Activity, TrendingUp, AlertTriangle, BarChart3, RefreshCw } from 'lucide-react';

interface BotHealth {
  botName: string;
  lastHeartbeat: string | null;
  uptime: number;
  errors24h: number;
  currentRegime: string;
  activeStrategies: number;
  portfolioHeat: number;
  status: string;
}

interface StrategyPerformance {
  strategy: string;
  pnlToday: number;
  pnlWeek: number;
  pnlMonth: number;
  pnlAllTime: number;
  winRate: number;
  sharpeRatio: number;
  activePositions: number;
  status: string;
}

interface RiskMetrics {
  portfolioHeat: number;
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
  confidence: number;
  trend: string;
  volatility: number;
  marketBreadth: number;
  vix: number;
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
        return 'text-yellow-400';
      case 'error':
      case 'stopped':
        return 'text-red-400';
      default:
        return 'text-gray-400';
    }
  };

  const getRegimeColor = (regime: string) => {
    if (!regime) return 'bg-gray-500/20 text-gray-400 border-gray-500/50';
    switch (regime.toLowerCase()) {
      case 'bull':
        return 'bg-green-500/20 text-green-400 border-green-500/50';
      case 'bear':
        return 'bg-red-500/20 text-red-400 border-red-500/50';
      case 'high_vol':
        return 'bg-orange-500/20 text-orange-400 border-orange-500/50';
      case 'low_vol':
        return 'bg-blue-500/20 text-blue-400 border-blue-500/50';
      case 'crisis':
        return 'bg-purple-500/20 text-purple-400 border-purple-500/50';
      default:
        return 'bg-gray-500/20 text-gray-400 border-gray-500/50';
    }
  };

  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value);
  };

  const formatPercent = (value: number) => {
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
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {botHealth.map((bot) => (
                  <div key={bot.botName} className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-white">{bot.botName}</h3>
                      <span className={`text-sm font-medium ${getStatusColor(bot.status)}`}>
                        {bot.status}
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-xs text-slate-400">Uptime</p>
                        <p className="text-sm font-medium text-white">{formatUptime(bot.uptime)}</p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-400">Errors (24h)</p>
                        <p className={`text-sm font-medium ${bot.errors24h > 0 ? 'text-red-400' : 'text-green-400'}`}>
                          {bot.errors24h}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-400">Active Strategies</p>
                        <p className="text-sm font-medium text-white">{bot.activeStrategies}</p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-400">Portfolio Heat</p>
                        <p className="text-sm font-medium text-white">{formatPercent(bot.portfolioHeat)}</p>
                      </div>
                    </div>
                    <div className="mt-4 pt-4 border-t border-slate-700">
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-slate-400">Current Regime</span>
                        <span className={`px-2 py-1 rounded text-xs font-medium border ${getRegimeColor(bot.currentRegime)}`}>
                          {bot.currentRegime}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
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
                        <th className="px-6 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">Today</th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">Week</th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">Month</th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">All Time</th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">Win Rate</th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">Sharpe</th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">Positions</th>
                        <th className="px-6 py-3 text-center text-xs font-medium text-slate-400 uppercase tracking-wider">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-700">
                      {strategyPerformance.map((strategy) => (
                        <tr key={strategy.strategy} className="hover:bg-slate-700/30">
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">
                            {strategy.strategy}
                          </td>
                          <td className={`px-6 py-4 whitespace-nowrap text-sm text-right ${strategy.pnlToday >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                            {formatCurrency(strategy.pnlToday)}
                          </td>
                          <td className={`px-6 py-4 whitespace-nowrap text-sm text-right ${strategy.pnlWeek >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                            {formatCurrency(strategy.pnlWeek)}
                          </td>
                          <td className={`px-6 py-4 whitespace-nowrap text-sm text-right ${strategy.pnlMonth >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                            {formatCurrency(strategy.pnlMonth)}
                          </td>
                          <td className={`px-6 py-4 whitespace-nowrap text-sm text-right ${strategy.pnlAllTime >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                            {formatCurrency(strategy.pnlAllTime)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-white">
                            {formatPercent(strategy.winRate)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-white">
                            {strategy.sharpeRatio.toFixed(2)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-white">
                            {strategy.activePositions}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-center">
                            <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(strategy.status)}`}>
                              {strategy.status}
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
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-sm text-slate-400">Portfolio Heat</p>
                      <p className="text-xs text-slate-500">{formatPercent(riskMetrics.maxPortfolioHeat)} max</p>
                    </div>
                    <div className="mb-2">
                      <p className="text-2xl font-bold text-white">{formatPercent(riskMetrics.portfolioHeat)}</p>
                    </div>
                    <div className="w-full bg-slate-700 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${riskMetrics.portfolioHeat / riskMetrics.maxPortfolioHeat > 0.8 ? 'bg-red-500' : riskMetrics.portfolioHeat / riskMetrics.maxPortfolioHeat > 0.6 ? 'bg-yellow-500' : 'bg-green-500'}`}
                        style={{ width: `${(riskMetrics.portfolioHeat / riskMetrics.maxPortfolioHeat) * 100}%` }}
                      />
                    </div>
                  </div>

                  <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-sm text-slate-400">Max Drawdown</p>
                      <p className="text-xs text-slate-500">{formatPercent(riskMetrics.maxDrawdownLimit)} limit</p>
                    </div>
                    <div className="mb-2">
                      <p className="text-2xl font-bold text-white">{formatPercent(riskMetrics.maxDrawdown)}</p>
                    </div>
                    <div className="w-full bg-slate-700 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${riskMetrics.maxDrawdown / riskMetrics.maxDrawdownLimit > 0.8 ? 'bg-red-500' : riskMetrics.maxDrawdown / riskMetrics.maxDrawdownLimit > 0.6 ? 'bg-yellow-500' : 'bg-green-500'}`}
                        style={{ width: `${(riskMetrics.maxDrawdown / riskMetrics.maxDrawdownLimit) * 100}%` }}
                      />
                    </div>
                  </div>

                  <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-sm text-slate-400">Daily P&L</p>
                      <p className="text-xs text-slate-500">{formatCurrency(riskMetrics.dailyLossLimit)} limit</p>
                    </div>
                    <div className="mb-2">
                      <p className={`text-2xl font-bold ${riskMetrics.dailyPnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {formatCurrency(riskMetrics.dailyPnl)}
                      </p>
                    </div>
                    <div className="w-full bg-slate-700 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${Math.abs(riskMetrics.dailyPnl) / riskMetrics.dailyLossLimit > 0.8 ? 'bg-red-500' : Math.abs(riskMetrics.dailyPnl) / riskMetrics.dailyLossLimit > 0.6 ? 'bg-yellow-500' : 'bg-green-500'}`}
                        style={{ width: `${Math.min((Math.abs(riskMetrics.dailyPnl) / riskMetrics.dailyLossLimit) * 100, 100)}%` }}
                      />
                    </div>
                  </div>

                  <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-sm text-slate-400">Open Positions</p>
                      <p className="text-xs text-slate-500">{riskMetrics.maxPositions} max</p>
                    </div>
                    <div className="mb-2">
                      <p className="text-2xl font-bold text-white">{riskMetrics.openPositions}</p>
                    </div>
                    <div className="w-full bg-slate-700 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${riskMetrics.openPositions / riskMetrics.maxPositions > 0.8 ? 'bg-red-500' : riskMetrics.openPositions / riskMetrics.maxPositions > 0.6 ? 'bg-yellow-500' : 'bg-green-500'}`}
                        style={{ width: `${(riskMetrics.openPositions / riskMetrics.maxPositions) * 100}%` }}
                      />
                    </div>
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
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                    <p className="text-sm text-slate-400 mb-2">Current Regime</p>
                    <div className="flex items-center justify-between">
                      <span className={`px-3 py-2 rounded-lg text-lg font-semibold border ${getRegimeColor(marketRegime.regime)}`}>
                        {marketRegime.regime}
                      </span>
                      <div className="text-right">
                        <p className="text-xs text-slate-400">Confidence</p>
                        <p className="text-lg font-bold text-white">{formatPercent(marketRegime.confidence)}</p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                    <p className="text-sm text-slate-400 mb-2">Trend</p>
                    <p className="text-2xl font-bold text-white">{marketRegime.trend}</p>
                    <p className="text-xs text-slate-500 mt-1">50-day SMA slope</p>
                  </div>

                  <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                    <p className="text-sm text-slate-400 mb-2">Volatility</p>
                    <p className="text-2xl font-bold text-white">{marketRegime.volatility.toFixed(2)}</p>
                    <p className="text-xs text-slate-500 mt-1">ATR ratio</p>
                  </div>

                  <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                    <p className="text-sm text-slate-400 mb-2">Market Breadth</p>
                    <p className="text-2xl font-bold text-white">{formatPercent(marketRegime.marketBreadth)}</p>
                    <p className="text-xs text-slate-500 mt-1">Above 200-day MA</p>
                  </div>

                  <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                    <p className="text-sm text-slate-400 mb-2">VIX Level</p>
                    <p className={`text-2xl font-bold ${marketRegime.vix > 30 ? 'text-red-400' : marketRegime.vix > 20 ? 'text-yellow-400' : 'text-green-400'}`}>
                      {marketRegime.vix.toFixed(2)}
                    </p>
                    <p className="text-xs text-slate-500 mt-1">Fear index</p>
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
