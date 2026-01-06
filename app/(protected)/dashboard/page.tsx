"use client";

import { useEffect, useState } from "react";
import { Navigation } from "@/components/navigation";
import { ReleaseBanner } from "@/components/release-banner";
import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";

interface BotStatus {
  status: string;
  lastHeartbeat: string;
  accountEquity: number;
  buyingPower: number;
  positionCount: number;
  openOrderCount: number;
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
        </div>
      </main>
    </div>
  );
}
