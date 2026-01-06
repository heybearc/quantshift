"use client";

import { useEffect, useState } from "react";
import { Navigation } from "@/components/navigation";
import { ReleaseBanner } from "@/components/release-banner";
import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";
import { TrendingUp, TrendingDown, DollarSign, Activity, AlertCircle } from "lucide-react";

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
              <p className="text-slate-400 mt-2">
                Real-time trading bot status and account overview
              </p>
            </div>

            {dataLoading ? (
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500"></div>
              </div>
            ) : (
              <>
                {botStatus?.errorMessage && (
                  <div className="bg-red-900/20 border border-red-700 rounded-xl p-4 flex items-start gap-3">
                    <AlertCircle className="h-5 w-5 text-red-500 mt-0.5" />
                    <div>
                      <h3 className="text-sm font-medium text-red-400">Bot Error</h3>
                      <p className="text-sm text-red-300 mt-1">{botStatus.errorMessage}</p>
                    </div>
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-sm font-medium text-slate-400">Bot Status</h3>
                      <Activity className="h-5 w-5 text-cyan-500" />
                    </div>
                    <p className={`text-2xl font-bold ${
                      botStatus?.status === "RUNNING" ? "text-green-500" :
                      botStatus?.status === "STALE" ? "text-yellow-500" :
                      "text-red-500"
                    }`}>
                      {botStatus?.status || "UNKNOWN"}
                    </p>
                    <p className="text-sm text-slate-400 mt-1">
                      {botStatus?.lastHeartbeat 
                        ? `Last update: ${new Date(botStatus.lastHeartbeat).toLocaleTimeString()}`
                        : "No heartbeat"}
                    </p>
                  </div>

                  <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-sm font-medium text-slate-400">Account Equity</h3>
                      <DollarSign className="h-5 w-5 text-cyan-500" />
                    </div>
                    <p className="text-2xl font-bold text-white">
                      {formatCurrency(botStatus?.accountEquity || 0)}
                    </p>
                    <p className="text-sm text-slate-400 mt-1">
                      Cash: {formatCurrency(botStatus?.accountCash || 0)}
                    </p>
                  </div>

                  <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-sm font-medium text-slate-400">Buying Power</h3>
                      <DollarSign className="h-5 w-5 text-cyan-500" />
                    </div>
                    <p className="text-2xl font-bold text-white">
                      {formatCurrency(botStatus?.buyingPower || 0)}
                    </p>
                    <p className="text-sm text-slate-400 mt-1">
                      Available for trading
                    </p>
                  </div>

                  <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-sm font-medium text-slate-400">Open Positions</h3>
                      <Activity className="h-5 w-5 text-cyan-500" />
                    </div>
                    <p className="text-2xl font-bold text-white">
                      {botStatus?.positionsCount || 0}
                    </p>
                    <p className="text-sm text-slate-400 mt-1">
                      Active trades
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-sm font-medium text-slate-400">Portfolio Value</h3>
                      <DollarSign className="h-5 w-5 text-cyan-500" />
                    </div>
                    <p className="text-2xl font-bold text-white">
                      {formatCurrency(botStatus?.portfolioValue || 0)}
                    </p>
                    <p className="text-sm text-slate-400 mt-1">Total portfolio</p>
                  </div>

                  <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-sm font-medium text-slate-400">Unrealized P&L</h3>
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
                    <p className="text-sm text-slate-400 mt-1">Open positions</p>
                  </div>

                  <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-sm font-medium text-slate-400">Realized P&L</h3>
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
                    <p className="text-sm text-slate-400 mt-1">Closed trades</p>
                  </div>
                </div>

                <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
                  <h3 className="text-lg font-medium text-white mb-4">Trading Activity</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-slate-400">Total Trades</p>
                      <p className="text-2xl font-bold text-white mt-1">{botStatus?.tradesCount || 0}</p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-400">Active Positions</p>
                      <p className="text-2xl font-bold text-white mt-1">{botStatus?.positionsCount || 0}</p>
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
