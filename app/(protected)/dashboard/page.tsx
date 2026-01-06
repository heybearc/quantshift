"use client";

import { ProtectedRoute } from "@/components/protected-route";
import { LayoutWrapper } from "@/components/layout-wrapper";
import { useEffect, useState } from "react";

interface BotStatus {
  status: string;
  lastHeartbeat: string;
  accountEquity: number;
  buyingPower: number;
  positionCount: number;
  openOrderCount: number;
}

export default function DashboardPage() {
  const [botStatus, setBotStatus] = useState<BotStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBotStatus();
    const interval = setInterval(fetchBotStatus, 30000);
    return () => clearInterval(interval);
  }, []);

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
      setLoading(false);
    }
  }

  return (
    <ProtectedRoute>
      <LayoutWrapper>
        <div className="space-y-6">
          <div>
            <h1 className="text-3xl font-bold text-white">Dashboard</h1>
            <p className="text-slate-400 mt-2">
              Real-time trading bot status and account overview
            </p>
          </div>

          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500"></div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
                <h3 className="text-sm font-medium text-slate-400 mb-2">Bot Status</h3>
                <p className="text-2xl font-bold text-white">
                  {botStatus?.status || "Unknown"}
                </p>
              </div>

              <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
                <h3 className="text-sm font-medium text-slate-400 mb-2">Account Equity</h3>
                <p className="text-2xl font-bold text-white">
                  ${botStatus?.accountEquity?.toFixed(2) || "0.00"}
                </p>
              </div>

              <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
                <h3 className="text-sm font-medium text-slate-400 mb-2">Buying Power</h3>
                <p className="text-2xl font-bold text-white">
                  ${botStatus?.buyingPower?.toFixed(2) || "0.00"}
                </p>
              </div>

              <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
                <h3 className="text-sm font-medium text-slate-400 mb-2">Open Positions</h3>
                <p className="text-2xl font-bold text-white">
                  {botStatus?.positionCount || 0}
                </p>
              </div>
            </div>
          )}
        </div>
      </LayoutWrapper>
    </ProtectedRoute>
  );
}
