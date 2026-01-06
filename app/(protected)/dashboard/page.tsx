"use client";

import { useEffect, useState } from "react";
import { Navigation } from "@/components/navigation";
import { ReleaseBanner } from "@/components/release-banner";
import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";
import { TrendingUp, TrendingDown, DollarSign, Activity, AlertCircle, Zap } from "lucide-react";

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

export default function DashboardPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [botStatus, setBotStatus] = useState<BotStatus | null>(null);
  const [dataLoading, setDataLoading] = useState(true);

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
  }, [user, loading, router]);

  useEffect(() => {
    if (user) {
      fetchBotStatus();
      const interval = setInterval(fetchBotStatus, 30000);
      return () => clearInterval(interval);
    }
  }, [user]);

  async function fetchBotStatus() {
    try {
      const response = await fetch("/api/bot/status");
      if (response.ok) {
        const data = await response.json();
        setBotStatus(data);
      }
    } catch (error) {
      console.error("Failed to fetch bot status:", error);
    } finally {
      setDataLoading(false);
    }
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
  };

  const totalPL = (botStatus?.unrealizedPl || 0) + (botStatus?.realizedPl || 0);
  const plPercent = botStatus?.accountEquity ? (totalPL / botStatus.accountEquity) * 100 : 0;

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
            {/* Header */}
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-white">Trading Dashboard</h1>
                <p className="text-slate-400 mt-1">Real-time account overview and bot status</p>
              </div>
              <div className="flex items-center gap-2 px-4 py-2 bg-slate-800/50 rounded-lg border border-slate-700">
                <div className={`h-2 w-2 rounded-full ${
                  botStatus?.status === "RUNNING" ? "bg-green-500 animate-pulse" :
                  botStatus?.status === "STALE" ? "bg-yellow-500" :
                  "bg-red-500"
                }`}></div>
                <span className="text-sm text-slate-300">
                  {botStatus?.status || "UNKNOWN"}
                </span>
              </div>
            </div>

            {botStatus?.errorMessage && (
              <div className="bg-red-900/20 border border-red-700 rounded-xl p-4 flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-red-500 mt-0.5 flex-shrink-0" />
                <div>
                  <h3 className="text-sm font-medium text-red-400">Bot Error</h3>
                  <p className="text-sm text-red-300 mt-1">{botStatus.errorMessage}</p>
                </div>
              </div>
            )}

            {dataLoading ? (
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500"></div>
              </div>
            ) : (
              <>
                {/* Primary Metrics - Large and Prominent */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {/* Account Equity - Most Important */}
                  <div className="lg:col-span-2 bg-gradient-to-br from-cyan-600 to-blue-600 rounded-2xl p-6 shadow-xl">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="text-cyan-100 text-sm font-medium mb-2">Account Equity</p>
                        <h2 className="text-5xl font-bold text-white mb-4">
                          {formatCurrency(botStatus?.accountEquity || 0)}
                        </h2>
                        <div className="flex items-center gap-4 text-sm">
                          <div>
                            <span className="text-cyan-100">Cash: </span>
                            <span className="text-white font-semibold">
                              {formatCurrency(botStatus?.accountCash || 0)}
                            </span>
                          </div>
                          <div className="h-4 w-px bg-cyan-400"></div>
                          <div>
                            <span className="text-cyan-100">Buying Power: </span>
                            <span className="text-white font-semibold">
                              {formatCurrency(botStatus?.buyingPower || 0)}
                            </span>
                          </div>
                        </div>
                      </div>
                      <DollarSign className="h-12 w-12 text-white/30" />
                    </div>
                  </div>

                  {/* Total P&L */}
                  <div className={`rounded-2xl p-6 shadow-xl ${
                    totalPL >= 0 
                      ? "bg-gradient-to-br from-green-600 to-emerald-600" 
                      : "bg-gradient-to-br from-red-600 to-rose-600"
                  }`}>
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="text-white/80 text-sm font-medium mb-2">Total P&L</p>
                        <h2 className="text-4xl font-bold text-white mb-2">
                          {formatCurrency(totalPL)}
                        </h2>
                        <div className="flex items-center gap-2">
                          {totalPL >= 0 ? (
                            <TrendingUp className="h-5 w-5 text-white" />
                          ) : (
                            <TrendingDown className="h-5 w-5 text-white" />
                          )}
                          <span className="text-xl font-semibold text-white">
                            {formatPercent(plPercent)}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Secondary Metrics - Quick Glance */}
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-5 border border-slate-700">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-slate-400 text-sm">Open Positions</span>
                      <Activity className="h-5 w-5 text-cyan-500" />
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

                  <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-5 border border-slate-700">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-slate-400 text-sm">Realized P&L</span>
                      {(botStatus?.realizedPl || 0) >= 0 ? (
                        <TrendingUp className="h-5 w-5 text-green-500" />
                      ) : (
                        <TrendingDown className="h-5 w-5 text-red-500" />
                      )}
                    </div>
                    <p className={`text-2xl font-bold ${
                      (botStatus?.realizedPl || 0) >= 0 ? "text-green-500" : "text-red-500"
                    }`}>
                      {formatCurrency(botStatus?.realizedPl || 0)}
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
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
