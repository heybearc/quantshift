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
  status: string;
  lastHeartbeat: string;
  accountEquity: number;
  accountCash: number;
  buyingPower: number;
  portfolioValue: number;
  unrealizedPl: number;
  realizedPl: number;
  positionsCount: number;
  tradesCount: number;
  errorMessage?: string;
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
  const [botStatus, setBotStatus] = useState<BotStatus | null>(null);
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
      fetchBotStatus();
      fetchBotMetrics();
      if (user.role?.toUpperCase() === 'ADMIN' || user.role?.toUpperCase() === 'SUPER_ADMIN') {
        fetchAdminStats();
      }
      const interval = setInterval(() => {
        fetchBotStatus();
        fetchBotMetrics();
        if (user.role?.toUpperCase() === 'ADMIN' || user.role?.toUpperCase() === 'SUPER_ADMIN') {
          fetchAdminStats();
        }
      }, 30000);
      return () => clearInterval(interval);
    }
  }, [user]);

  const fetchBotStatus = async () => {
    try {
      const response = await fetch("/api/bot/status");
      if (response.ok) {
        const data = await response.json();
        setBotStatus(data);
        setError(null);
      } else {
        setError("Failed to fetch bot status");
      }
    } catch (err) {
      setError("Error connecting to bot");
    } finally {
      setDataLoading(false);
    }
  };

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
                      {formatCurrency(botStatus?.accountEquity || 0)}
                    </p>
                    <p className="text-sm text-cyan-300">
                      Cash: {formatCurrency(botStatus?.accountCash || 0)}
                    </p>
                  </div>

                  <div className="bg-gradient-to-br from-purple-900/50 to-pink-900/50 backdrop-blur-sm rounded-xl p-6 border border-purple-700/50">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-purple-300 text-sm font-medium">Total P&L</span>
                      {((botStatus?.realizedPl || 0) + (botStatus?.unrealizedPl || 0)) >= 0 ? (
                        <TrendingUp className="h-6 w-6 text-green-400" />
                      ) : (
                        <TrendingDown className="h-6 w-6 text-red-400" />
                      )}
                    </div>
                    <p className={`text-4xl font-bold mb-2 ${
                      ((botStatus?.realizedPl || 0) + (botStatus?.unrealizedPl || 0)) >= 0 
                        ? "text-green-400" 
                        : "text-red-400"
                    }`}>
                      {formatCurrency((botStatus?.realizedPl || 0) + (botStatus?.unrealizedPl || 0))}
                    </p>
                    <p className="text-sm text-purple-300">
                      Realized: {formatCurrency(botStatus?.realizedPl || 0)}
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
                      {formatCurrency(botStatus?.buyingPower || 0)}
                    </p>
                  </div>

                  <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-5 border border-slate-700">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-slate-400 text-sm">Open Positions</span>
                      <TrendingUp className="h-5 w-5 text-purple-500" />
                    </div>
                    <p className="text-3xl font-bold text-white">{botStatus?.positionsCount || 0}</p>
                  </div>

                  <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-5 border border-slate-700">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-slate-400 text-sm">Total Trades</span>
                      <Zap className="h-5 w-5 text-cyan-500" />
                    </div>
                    <p className="text-3xl font-bold text-white">{botStatus?.tradesCount || 0}</p>
                  </div>

                  <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-5 border border-slate-700">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-slate-400 text-sm">Unrealized P&L</span>
                      {(botStatus?.unrealizedPl || 0) >= 0 ? (
                        <TrendingUp className="h-5 w-5 text-green-500" />
                      ) : (
                        <TrendingDown className="h-5 w-5 text-red-500" />
                      )}
                    </div>
                    <p className={`text-2xl font-bold ${
                      (botStatus?.unrealizedPl || 0) >= 0 ? "text-green-500" : "text-red-500"
                    }`}>
                      {formatCurrency(botStatus?.unrealizedPl || 0)}
                    </p>
                  </div>
                </div>

                {/* Bot Status Info */}
                <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
                  <h3 className="text-lg font-semibold text-white mb-4">Bot Status</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div>
                      <p className="text-sm text-slate-400 mb-1">Status</p>
                      <p className={`text-lg font-semibold ${
                        botStatus?.status === "RUNNING" ? "text-green-500" :
                        botStatus?.status === "STALE" ? "text-yellow-500" :
                        "text-red-500"
                      }`}>
                        {botStatus?.status || "UNKNOWN"}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-400 mb-1">Last Heartbeat</p>
                      <p className="text-lg font-semibold text-white">
                        {botStatus?.lastHeartbeat 
                          ? new Date(botStatus.lastHeartbeat).toLocaleTimeString()
                          : "No heartbeat"}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-400 mb-1">Portfolio Value</p>
                      <p className="text-lg font-semibold text-white">
                        {formatCurrency(botStatus?.portfolioValue || 0)}
                      </p>
                    </div>
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
