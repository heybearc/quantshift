"use client";

import { useEffect, useState } from "react";
import { Navigation } from "@/components/navigation";
import { ReleaseBanner } from "@/components/release-banner";
import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { TrendingUp, TrendingDown, DollarSign, Activity, AlertCircle, Zap, BarChart2, Bitcoin } from "lucide-react";
import { WinRateCard } from "@/components/dashboard/WinRateCard";
import { MaxDrawdownCard } from "@/components/dashboard/MaxDrawdownCard";
import { StrategyCard } from "@/components/dashboard/StrategyCard";
import { UsersStatsCard } from "@/components/dashboard/admin/UsersStatsCard";
import { SessionsStatsCard } from "@/components/dashboard/admin/SessionsStatsCard";
import { AuditStatsCard } from "@/components/dashboard/admin/AuditStatsCard";
import { SystemHealthCard } from "@/components/dashboard/admin/SystemHealthCard";

type BotTab = 'all' | 'equity-bot' | 'crypto-bot';

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
  users: { total: number; active: number; pending: number; inactive: number };
  sessions: { current: number; peakToday: number; avgDuration: number };
  auditLogs: { last24h: number; critical: number; warnings: number };
  systemHealth: { status: 'healthy' | 'degraded' | 'down'; apiResponseTime: number; databaseConnections: number; uptime: number };
}

export default function DashboardPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [allBotStatus, setAllBotStatus] = useState<BotStatus[]>([]);
  const [botMetrics, setBotMetrics] = useState<BotMetrics | null>(null);
  const [adminStats, setAdminStats] = useState<AdminStats | null>(null);
  const [dataLoading, setDataLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<BotTab>('all');

  useEffect(() => {
    if (!loading && !user) router.push("/login");
  }, [user, loading, router]);

  useEffect(() => {
    if (user) {
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
      const res = await fetch("/api/bot/status/all");
      if (res.ok) { setAllBotStatus((await res.json()).bots || []); setError(null); }
      else setError("Failed to fetch bot status");
    } catch { setError("Error connecting to bots"); }
    finally { setDataLoading(false); }
  };

  const fetchBotMetrics = async () => {
    try {
      const res = await fetch("/api/bot/metrics");
      if (res.ok) setBotMetrics(await res.json());
    } catch { /* silent */ }
  };

  const fetchAdminStats = async () => {
    try {
      const res = await fetch("/api/admin/stats");
      if (res.ok) setAdminStats(await res.json());
    } catch { /* silent */ }
  };

  const fmt = (v: number) => new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", minimumFractionDigits: 2 }).format(v);
  const fmtHb = (ts: string | null) => ts
    ? new Date(ts).toLocaleString('en-US', { timeZone: 'America/New_York', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true })
    : 'No heartbeat';

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center bg-slate-900">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500" />
    </div>
  );
  if (!user) return null;

  const equityBot = allBotStatus.find(b => b.botName === 'equity-bot');
  const cryptoBot = allBotStatus.find(b => b.botName === 'crypto-bot');
  const totalEquity = (equityBot?.accountEquity || 0) + (cryptoBot?.portfolioValue || 0);
  const totalPl = (equityBot?.realizedPl || 0) + (equityBot?.unrealizedPl || 0) + (cryptoBot?.unrealizedPl || 0);
  const totalPositions = (equityBot?.positionsCount || 0) + (cryptoBot?.positionsCount || 0);
  const totalTrades = (equityBot?.tradesCount || 0) + (cryptoBot?.tradesCount || 0);
  const isAdmin = user?.role?.toUpperCase() === 'ADMIN' || user?.role?.toUpperCase() === 'SUPER_ADMIN';

  const StatusDot = ({ status }: { status: string }) => {
    const running = status === 'RUNNING', stale = status === 'STALE';
    return (
      <div className="flex items-center gap-1.5">
        <span className={`w-2 h-2 rounded-full inline-block ${running ? 'bg-green-400 animate-pulse' : stale ? 'bg-yellow-400' : 'bg-red-400'}`} />
        <span className={`text-xs font-semibold ${running ? 'text-green-400' : stale ? 'text-yellow-400' : 'text-red-400'}`}>{status}</span>
      </div>
    );
  };

  const borderFor = (s: string) => s === 'RUNNING' ? 'border-green-700/40' : s === 'STALE' ? 'border-yellow-700/40' : 'border-slate-700';

  const BotDetail = ({ bot, isEquity }: { bot: BotStatus | undefined; isEquity: boolean }) => {
    if (!bot) return <div className="text-center text-slate-500 py-16">No data available yet — bot may not have heartbeated.</div>;
    return (
      <div className="space-y-4">
        <div className={`rounded-xl p-4 border flex items-center justify-between bg-slate-800/30 ${borderFor(bot.status)}`}>
          <div>
            <p className="text-white font-semibold">{isEquity ? 'Equity Bot' : 'Crypto Bot'}</p>
            <p className="text-slate-400 text-xs mt-0.5">
              {isEquity ? 'Alpaca Paper Trading · MA Crossover · 5/20 Daily SMA' : 'Coinbase Dry-Run · MA + RSI + MACD · 20/50 Hourly SMA'}
            </p>
          </div>
          <div className="text-right">
            <StatusDot status={bot.status} />
            <p className="text-slate-500 text-xs mt-1">Heartbeat: {fmtHb(bot.lastHeartbeat)}</p>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
            <p className="text-slate-400 text-xs mb-1">Portfolio Value</p>
            <p className="text-white text-xl font-bold">{fmt(bot.portfolioValue)}</p>
            <p className="text-slate-500 text-xs mt-1">{isEquity ? `Cash: ${fmt(bot.accountCash)}` : 'Paper balance'}</p>
          </div>
          <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
            <p className="text-slate-400 text-xs mb-1">Unrealized P&L</p>
            <p className={`text-xl font-bold ${bot.unrealizedPl >= 0 ? 'text-green-400' : 'text-red-400'}`}>{fmt(bot.unrealizedPl)}</p>
            {isEquity && <p className="text-slate-500 text-xs mt-1">Realized: {fmt(bot.realizedPl)}</p>}
          </div>
          <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
            <p className="text-slate-400 text-xs mb-1">Open Positions</p>
            <p className="text-white text-xl font-bold">{bot.positionsCount}</p>
            <p className="text-slate-500 text-xs mt-1">{isEquity ? 'Max 5 allowed' : 'Max 3 allowed'}</p>
          </div>
          <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
            <p className="text-slate-400 text-xs mb-1">Total Trades</p>
            <p className="text-white text-xl font-bold">{bot.tradesCount}</p>
            <p className="text-slate-500 text-xs mt-1">All time</p>
          </div>
        </div>

        {isEquity && (
          <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700 flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-xs">Buying Power</p>
              <p className="text-white text-lg font-bold">{fmt(bot.buyingPower)}</p>
            </div>
            <Activity className="h-5 w-5 text-blue-400" />
          </div>
        )}

        {botMetrics && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <WinRateCard winRate={botMetrics.winRate} totalWins={botMetrics.totalWins} totalLosses={botMetrics.totalLosses} totalTrades={botMetrics.totalTrades} />
            <MaxDrawdownCard maxDrawdown={botMetrics.maxDrawdown} maxDrawdownAmount={botMetrics.maxDrawdownAmount} formatCurrency={fmt} />
            <StrategyCard currentStrategy={botMetrics.currentStrategy} strategySuccessRate={botMetrics.strategySuccessRate} avgTradesPerDay={botMetrics.avgTradesPerDay} />
          </div>
        )}

        {bot.errorMessage && (
          <div className="bg-red-900/20 border border-red-700/50 rounded-xl p-4 flex items-start gap-3">
            <AlertCircle className="h-4 w-4 text-red-400 mt-0.5 shrink-0" />
            <p className="text-red-400 text-sm">{bot.errorMessage}</p>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="flex h-screen bg-slate-900">
      <Navigation />
      <main className="flex-1 lg:ml-64 overflow-y-auto">
        {user && <ReleaseBanner userId={user.id} />}
        <div className="p-8">
          <div className="space-y-6">

            <div>
              <h1 className="text-3xl font-bold text-white">Dashboard</h1>
              <p className="text-slate-400 mt-1">Live performance across all trading bots</p>
            </div>

            {error && (
              <div className="bg-red-900/20 border border-red-700 rounded-xl p-4 flex items-center gap-3">
                <AlertCircle className="h-5 w-5 text-red-400" />
                <p className="text-red-400">{error}</p>
              </div>
            )}

            {dataLoading ? (
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500" />
              </div>
            ) : (
              <>
                {/* COMBINED PORTFOLIO HEADER — always visible */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-gradient-to-br from-cyan-900/50 to-blue-900/50 rounded-xl p-5 border border-cyan-700/50">
                    <p className="text-cyan-300 text-xs font-medium mb-1">Total Portfolio</p>
                    <p className="text-white text-2xl font-bold">{fmt(totalEquity)}</p>
                    <p className="text-cyan-400 text-xs mt-1">Both bots combined</p>
                  </div>
                  <div className="bg-gradient-to-br from-purple-900/50 to-pink-900/50 rounded-xl p-5 border border-purple-700/50">
                    <p className="text-purple-300 text-xs font-medium mb-1">Total P&L</p>
                    <p className={`text-2xl font-bold ${totalPl >= 0 ? 'text-green-400' : 'text-red-400'}`}>{fmt(totalPl)}</p>
                    <p className="text-purple-400 text-xs mt-1">Realized + unrealized</p>
                  </div>
                  <div className="bg-slate-800/50 rounded-xl p-5 border border-slate-700">
                    <p className="text-slate-400 text-xs font-medium mb-1">Open Positions</p>
                    <p className="text-white text-2xl font-bold">{totalPositions}</p>
                    <p className="text-slate-500 text-xs mt-1">Across all bots</p>
                  </div>
                  <div className="bg-slate-800/50 rounded-xl p-5 border border-slate-700">
                    <p className="text-slate-400 text-xs font-medium mb-1">Total Trades</p>
                    <p className="text-white text-2xl font-bold">{totalTrades}</p>
                    <p className="text-slate-500 text-xs mt-1">All time, all bots</p>
                  </div>
                </div>

                {/* BOT TAB SWITCHER */}
                <div>
                  <div className="flex items-center gap-1 bg-slate-800/50 rounded-xl p-1 border border-slate-700 w-fit mb-4">
                    {([
                      { id: 'all' as BotTab, label: 'All Bots', icon: null, bot: undefined },
                      { id: 'equity-bot' as BotTab, label: 'Equity Bot', icon: <BarChart2 className="h-3.5 w-3.5" />, bot: equityBot },
                      { id: 'crypto-bot' as BotTab, label: 'Crypto Bot', icon: <Bitcoin className="h-3.5 w-3.5" />, bot: cryptoBot },
                    ]).map(({ id, label, icon, bot }) => (
                      <button
                        key={id}
                        onClick={() => setActiveTab(id)}
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                          activeTab === id ? 'bg-cyan-600 text-white shadow' : 'text-slate-400 hover:text-white hover:bg-slate-700'
                        }`}
                      >
                        {icon}
                        {label}
                        {bot && (
                          <span className={`w-1.5 h-1.5 rounded-full inline-block ${
                            bot.status === 'RUNNING' ? 'bg-green-400' : bot.status === 'STALE' ? 'bg-yellow-400' : 'bg-red-400'
                          }`} />
                        )}
                      </button>
                    ))}
                  </div>

                  {/* ALL BOTS — side-by-side summary */}
                  {activeTab === 'all' && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {([
                        { bot: equityBot, isEquity: true, tab: 'equity-bot' as BotTab, label: 'Equity Bot', sub: 'Alpaca Paper · MA Crossover · Daily', iconBg: 'bg-blue-900/50 border-blue-700/50', icon: <BarChart2 className="h-5 w-5 text-blue-400" /> },
                        { bot: cryptoBot, isEquity: false, tab: 'crypto-bot' as BotTab, label: 'Crypto Bot', sub: 'Coinbase Dry-Run · MA/RSI/MACD · Hourly', iconBg: 'bg-orange-900/50 border-orange-700/50', icon: <Bitcoin className="h-5 w-5 text-orange-400" /> },
                      ]).map(({ bot, isEquity, tab, label, sub, iconBg, icon }) => (
                        <div key={tab} className={`bg-slate-800/50 rounded-xl p-5 border ${borderFor(bot?.status || 'UNKNOWN')}`}>
                          <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center gap-3">
                              <div className={`w-9 h-9 rounded-lg border flex items-center justify-center ${iconBg}`}>{icon}</div>
                              <div>
                                <p className="text-white font-semibold text-sm">{label}</p>
                                <p className="text-slate-500 text-xs">{sub}</p>
                              </div>
                            </div>
                            <StatusDot status={bot?.status || 'UNKNOWN'} />
                          </div>
                          <div className="grid grid-cols-3 gap-3 mb-4">
                            <div>
                              <p className="text-slate-400 text-xs">Portfolio</p>
                              <p className="text-white font-semibold text-sm">{fmt(bot?.portfolioValue || 0)}</p>
                            </div>
                            <div>
                              <p className="text-slate-400 text-xs">P&L</p>
                              <p className={`font-semibold text-sm ${((bot?.unrealizedPl || 0) + (isEquity ? (bot?.realizedPl || 0) : 0)) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                {fmt((bot?.unrealizedPl || 0) + (isEquity ? (bot?.realizedPl || 0) : 0))}
                              </p>
                            </div>
                            <div>
                              <p className="text-slate-400 text-xs">Positions</p>
                              <p className="text-white font-semibold text-sm">{bot?.positionsCount || 0}</p>
                            </div>
                          </div>
                          <div className="flex items-center justify-between border-t border-slate-700 pt-3">
                            <p className="text-slate-600 text-xs">Heartbeat: {fmtHb(bot?.lastHeartbeat || null)}</p>
                            <button onClick={() => setActiveTab(tab)} className="text-xs text-cyan-400 hover:text-cyan-300 transition-colors">
                              View details →
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {activeTab === 'equity-bot' && <BotDetail bot={equityBot} isEquity={true} />}
                  {activeTab === 'crypto-bot' && <BotDetail bot={cryptoBot} isEquity={false} />}
                </div>

                {/* ADMIN SYSTEM OVERVIEW — bottom, admin only */}
                {isAdmin && adminStats && (
                  <div>
                    <h2 className="text-lg font-semibold text-white mb-4">System Overview</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                      <UsersStatsCard total={adminStats.users.total} active={adminStats.users.active} pending={adminStats.users.pending} inactive={adminStats.users.inactive} />
                      <SessionsStatsCard current={adminStats.sessions.current} peakToday={adminStats.sessions.peakToday} avgDuration={adminStats.sessions.avgDuration} />
                      <AuditStatsCard last24h={adminStats.auditLogs.last24h} critical={adminStats.auditLogs.critical} warnings={adminStats.auditLogs.warnings} />
                      <SystemHealthCard status={adminStats.systemHealth.status} apiResponseTime={adminStats.systemHealth.apiResponseTime} databaseConnections={adminStats.systemHealth.databaseConnections} />
                    </div>
                  </div>
                )}

                {/* QUICK ACTIONS */}
                <div className="flex flex-wrap gap-3">
                  <Link href="/trades" className="px-4 py-2 text-sm font-medium text-white bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors">View Trades</Link>
                  <Link href="/performance" className="px-4 py-2 text-sm font-medium text-white bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors">Performance</Link>
                  <Link href="/settings/notifications" className="px-4 py-2 text-sm font-medium text-white bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors">Email Settings</Link>
                  {isAdmin && <Link href="/users" className="px-4 py-2 text-sm font-medium text-white bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors">User Management</Link>}
                </div>
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
