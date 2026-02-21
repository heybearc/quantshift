"use client";

import { useEffect, useState } from "react";
import { Navigation } from "@/components/navigation";
import { ReleaseBanner } from "@/components/release-banner";
import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { TrendingUp, TrendingDown, DollarSign, Activity, AlertCircle, Zap } from "lucide-react";
import { WinRateCard } from "@/components/dashboard/WinRateCard";
import { MaxDrawdownCard } from "@/components/dashboard/MaxDrawdownCard";
import { StrategyCard } from "@/components/dashboard/StrategyCard";
import { UsersStatsCard } from "@/components/dashboard/admin/UsersStatsCard";
import { SessionsStatsCard } from "@/components/dashboard/admin/SessionsStatsCard";
import { AuditStatsCard } from "@/components/dashboard/admin/AuditStatsCard";
import { SystemHealthCard } from "@/components/dashboard/admin/SystemHealthCard";

interface BotStatus {
  botName: string;
  status: string;
  lastHeartbeat: string | null;
  accountEquity: number;
  accountCash: number;
  buyingPower: number;
  portfolioValue: number;
  unrealizedPl: number;
  realizedPl: number;
  positionsCount: number;
  tradesCount: number;
  errorMessage?: string | null;
}

interface BotMetrics {
  winRate: number;
  totalWins: number;
  totalLosses: number;
  totalTrades: number;
  maxDrawdown: number;
  maxDrawdownAmount: number;
  avgTradesPerDay: number;
  lastTradeTime: string | null;
  currentStrategy: string;
  strategySuccessRate: number;
}

interface AdminStats {
  users: {
    total: number;
    active: number;
    pending: number;
    inactive: number;
  };
  sessions: {
    current: number;
    peakToday: number;
    avgDuration: number;
  };
  auditLogs: {
    last24h: number;
    critical: number;
    warnings: number;
  };
  systemHealth: {
    status: 'healthy' | 'degraded' | 'down';
    apiResponseTime: number;
    databaseConnections: number;
    uptime: number;
  };
}

export default function DashboardPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [allBotStatus, setAllBotStatus] = useState<BotStatus[]>([]);
  const [botMetrics, setBotMetrics] = useState<BotMetrics | null>(null);
  const [adminStats, setAdminStats] = useState<AdminStats | null>(null);
  const [dataLoading, setDataLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
  }, [user, loading, router]);

  useEffect(() => {
    if (user) {
      console.log('[Dashboard] User role:', user.role);
      console.log('[Dashboard] Is admin?', user.role?.toUpperCase() === 'ADMIN' || user.role?.toUpperCase() === 'SUPER_ADMIN');
      fetchAllBotStatus();
      fetchBotMetrics();
      if (user.role?.toUpperCase() === 'ADMIN' || user.role?.toUpperCase() === 'SUPER_ADMIN') {
        fetchAdminStats();
      }
      const interval = setInterval(() => {
        fetchAllBotStatus();
        fetchBotMetrics();
        if (user.role?.toUpperCase() === 'ADMIN' || user.role?.toUpperCase() === 'SUPER_ADMIN') {
          fetchAdminStats();
        }
      }, 30000);
      return () => clearInterval(interval);
    }
  }, [user]);

  const fetchAllBotStatus = async () => {
    try {
      const response = await fetch("/api/bot/status/all");
      if (response.ok) {
        const data = await response.json();
        setAllBotStatus(data.bots || []);
        setError(null);
      } else {
        setError("Failed to fetch bot status");
      }
    } catch (err) {
      setError("Error connecting to bots");
    } finally {
      setDataLoading(false);
    }
  };

  const equityBot = allBotStatus.find(b => b.botName === 'equity-bot');
  const cryptoBot = allBotStatus.find(b => b.botName === 'crypto-bot');

  const fetchBotMetrics = async () => {
    try {
      const response = await fetch("/api/bot/metrics");
      if (response.ok) {
        const data = await response.json();
        setBotMetrics(data);
      }
    } catch (err) {
      console.error("Error fetching bot metrics:", err);
    }
  };

  const fetchAdminStats = async () => {
    try {
      console.log('[Dashboard] Fetching admin stats...');
      const response = await fetch("/api/admin/stats");
      console.log('[Dashboard] Admin stats response status:', response.status);
      if (response.ok) {
        const data = await response.json();
        console.log('[Dashboard] Admin stats data:', data);
        setAdminStats(data);
      } else {
        const error = await response.json();
        console.error('[Dashboard] Admin stats error:', error);
      }
    } catch (err) {
      console.error("Error fetching admin stats:", err);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-900">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500"></div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="flex h-screen bg-slate-900">
      <Navigation />
      <main className="flex-1 lg:ml-64 overflow-y-auto">
        {user && <ReleaseBanner userId={user.id} />}
        <div className="p-8">
          <div className="space-y-6">
            <div>
              <h1 className="text-3xl font-bold text-white">Dashboard</h1>
              <p className="text-slate-400 mt-2">Monitor your bot performance and account metrics</p>
            </div>

            {error && (
              <div className="bg-red-900/20 border border-red-700 rounded-xl p-4 flex items-center gap-3">
                <AlertCircle className="h-5 w-5 text-red-400" />
                <p className="text-red-400">{error}</p>
              </div>
            )}

            {dataLoading ? (
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500"></div>
              </div>
            ) : (
              <>
                {/* Primary Metrics */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="bg-gradient-to-br from-cyan-900/50 to-blue-900/50 backdrop-blur-sm rounded-xl p-6 border border-cyan-700/50">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-cyan-300 text-sm font-medium">Account Equity</span>
                      <DollarSign className="h-6 w-6 text-cyan-400" />
                    </div>
                    <p className="text-4xl font-bold text-white mb-2">
                      {formatCurrency(equityBot?.accountEquity || 0)}
                    </p>
                    <p className="text-sm text-cyan-300">
                      Cash: {formatCurrency(equityBot?.accountCash || 0)}
                    </p>
                  </div>

                  <div className="bg-gradient-to-br from-purple-900/50 to-pink-900/50 backdrop-blur-sm rounded-xl p-6 border border-purple-700/50">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-purple-300 text-sm font-medium">Total P&L</span>
                      {((equityBot?.realizedPl || 0) + (equityBot?.unrealizedPl || 0)) >= 0 ? (
                        <TrendingUp className="h-6 w-6 text-green-400" />
                      ) : (
                        <TrendingDown className="h-6 w-6 text-red-400" />
                      )}
                    </div>
                    <p className={`text-4xl font-bold mb-2 ${
                      ((equityBot?.realizedPl || 0) + (equityBot?.unrealizedPl || 0)) >= 0 
                        ? "text-green-400" 
                        : "text-red-400"
                    }`}>
                      {formatCurrency((equityBot?.realizedPl || 0) + (equityBot?.unrealizedPl || 0))}
                    </p>
                    <p className="text-sm text-purple-300">
                      Realized: {formatCurrency(equityBot?.realizedPl || 0)}
                    </p>
                  </div>
                </div>

                {/* Enhanced Trading Metrics */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {botMetrics && (
                    <>
                      <WinRateCard
                        winRate={botMetrics.winRate}
                        totalWins={botMetrics.totalWins}
                        totalLosses={botMetrics.totalLosses}
                        totalTrades={botMetrics.totalTrades}
                      />
                      <MaxDrawdownCard
                        maxDrawdown={botMetrics.maxDrawdown}
                        maxDrawdownAmount={botMetrics.maxDrawdownAmount}
                        formatCurrency={formatCurrency}
                      />
                      <StrategyCard
                        currentStrategy={botMetrics.currentStrategy}
                        strategySuccessRate={botMetrics.strategySuccessRate}
                        avgTradesPerDay={botMetrics.avgTradesPerDay}
                      />
                    </>
                  )}
                </div>

                {/* Secondary Metrics - Quick Glance */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-5 border border-slate-700">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-slate-400 text-sm">Buying Power</span>
                      <Activity className="h-5 w-5 text-blue-500" />
                    </div>
                    <p className="text-2xl font-bold text-white">
                      {formatCurrency(equityBot?.buyingPower || 0)}
                    </p>
                  </div>

                  <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-5 border border-slate-700">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-slate-400 text-sm">Open Positions</span>
                      <TrendingUp className="h-5 w-5 text-purple-500" />
                    </div>
                    <p className="text-3xl font-bold text-white">
                      {(equityBot?.positionsCount || 0) + (cryptoBot?.positionsCount || 0)}
                    </p>
                  </div>

                  <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-5 border border-slate-700">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-slate-400 text-sm">Total Trades</span>
                      <Zap className="h-5 w-5 text-cyan-500" />
                    </div>
                    <p className="text-3xl font-bold text-white">
                      {(equityBot?.tradesCount || 0) + (cryptoBot?.tradesCount || 0)}
                    </p>
                  </div>

                  <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-5 border border-slate-700">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-slate-400 text-sm">Unrealized P&L</span>
                      {((equityBot?.unrealizedPl || 0) + (cryptoBot?.unrealizedPl || 0)) >= 0 ? (
                        <TrendingUp className="h-5 w-5 text-green-500" />
                      ) : (
                        <TrendingDown className="h-5 w-5 text-red-500" />
                      )}
                    </div>
                    <p className={`text-2xl font-bold ${
                      ((equityBot?.unrealizedPl || 0) + (cryptoBot?.unrealizedPl || 0)) >= 0 ? "text-green-500" : "text-red-500"
                    }`}>
                      {formatCurrency((equityBot?.unrealizedPl || 0) + (cryptoBot?.unrealizedPl || 0))}
                    </p>
                  </div>
                </div>

                {/* Active Bots */}
                <div>
                  <h3 className="text-lg font-semibold text-white mb-4">Active Bots</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {[equityBot, cryptoBot].map((bot) => {
                      if (!bot) return null;
                      const isRunning = bot.status === 'RUNNING';
                      const isStale = bot.status === 'STALE';
                      const label = bot.botName === 'equity-bot' ? 'Equity Bot' : 'Crypto Bot';
                      const subtitle = bot.botName === 'equity-bot' ? 'Alpaca Paper · MA Crossover' : 'Coinbase · MA/RSI/MACD';
                      const borderColor = isRunning ? 'border-green-700/50' : isStale ? 'border-yellow-700/50' : 'border-red-700/50';
                      const statusColor = isRunning ? 'text-green-400' : isStale ? 'text-yellow-400' : 'text-red-400';
                      const dotColor = isRunning ? 'bg-green-400' : isStale ? 'bg-yellow-400' : 'bg-red-400';
                      return (
                        <div key={bot.botName} className={`bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border ${borderColor}`}>
                          <div className="flex items-start justify-between mb-4">
                            <div>
                              <h4 className="text-white font-semibold text-base">{label}</h4>
                              <p className="text-slate-400 text-xs mt-0.5">{subtitle}</p>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className={`inline-block w-2 h-2 rounded-full ${dotColor} ${isRunning ? 'animate-pulse' : ''}`} />
                              <span className={`text-sm font-semibold ${statusColor}`}>{bot.status}</span>
                            </div>
                          </div>
                          <div className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
                            <div>
                              <p className="text-slate-400 text-xs">Portfolio Value</p>
                              <p className="text-white font-semibold">{formatCurrency(bot.portfolioValue)}</p>
                            </div>
                            <div>
                              <p className="text-slate-400 text-xs">Unrealized P&L</p>
                              <p className={`font-semibold ${ bot.unrealizedPl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                {formatCurrency(bot.unrealizedPl)}
                              </p>
                            </div>
                            <div>
                              <p className="text-slate-400 text-xs">Open Positions</p>
                              <p className="text-white font-semibold">{bot.positionsCount}</p>
                            </div>
                            <div>
                              <p className="text-slate-400 text-xs">Total Trades</p>
                              <p className="text-white font-semibold">{bot.tradesCount}</p>
                            </div>
                            <div className="col-span-2">
                              <p className="text-slate-400 text-xs">Last Heartbeat</p>
                              <p className="text-white font-medium">
                                {bot.lastHeartbeat
                                  ? new Date(bot.lastHeartbeat).toLocaleString('en-US', { timeZone: 'America/New_York', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true })
                                  : 'No heartbeat'}
                              </p>
                            </div>
                            {bot.errorMessage && (
                              <div className="col-span-2">
                                <p className="text-red-400 text-xs truncate">{bot.errorMessage}</p>
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Admin Statistics Section */}
                {(() => {
                  const isAdmin = user?.role?.toUpperCase() === 'ADMIN' || user?.role?.toUpperCase() === 'SUPER_ADMIN';
                  console.log('[Dashboard] Render check - isAdmin:', isAdmin, 'hasAdminStats:', !!adminStats);
                  return isAdmin && adminStats;
                })() && adminStats && (
                  <>
                    <div className="mt-8">
                      <h2 className="text-2xl font-bold text-white mb-4">System Overview</h2>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        <UsersStatsCard
                          total={adminStats.users.total}
                          active={adminStats.users.active}
                          pending={adminStats.users.pending}
                          inactive={adminStats.users.inactive}
                        />
                        <SessionsStatsCard
                          current={adminStats.sessions.current}
                          peakToday={adminStats.sessions.peakToday}
                          avgDuration={adminStats.sessions.avgDuration}
                        />
                        <AuditStatsCard
                          last24h={adminStats.auditLogs.last24h}
                          critical={adminStats.auditLogs.critical}
                          warnings={adminStats.auditLogs.warnings}
                        />
                        <SystemHealthCard
                          status={adminStats.systemHealth.status}
                          apiResponseTime={adminStats.systemHealth.apiResponseTime}
                          databaseConnections={adminStats.systemHealth.databaseConnections}
                        />
                      </div>
                    </div>
                  </>
                )}

                {/* Quick Actions */}
                <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6">
                  <h3 className="text-lg font-semibold text-white mb-4">Quick Actions</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <Link
                      href="/trades"
                      className="px-4 py-3 text-sm font-medium text-white bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors text-center"
                    >
                      View Trades
                    </Link>
                    <Link
                      href="/performance"
                      className="px-4 py-3 text-sm font-medium text-white bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors text-center"
                    >
                      Performance
                    </Link>
                    <Link
                      href="/settings/notifications"
                      className="px-4 py-3 text-sm font-medium text-white bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors text-center"
                    >
                      Email Settings
                    </Link>
                    {user?.role?.toUpperCase() === "ADMIN" && (
                      <Link
                        href="/users"
                        className="px-4 py-3 text-sm font-medium text-white bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors text-center"
                      >
                        User Management
                      </Link>
                    )}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
