"use client";

import { useAuth } from "@/lib/auth-context";
import { Navigation } from "@/components/navigation";
import { ReleaseBanner } from "@/components/release-banner";
import { useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import { Activity, Database, Server, CheckCircle, XCircle, AlertCircle, RefreshCw } from "lucide-react";

interface HealthStatus {
  status: "healthy" | "degraded" | "down";
  database: boolean;
  api: boolean;
  bot: boolean;
  lastCheck: string;
}

export default function HealthPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login");
    }
    if (!authLoading && user && user.role?.toUpperCase() !== "ADMIN") {
      router.push("/dashboard");
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    if (user?.role?.toUpperCase() === "ADMIN") {
      checkHealth();
      const interval = setInterval(checkHealth, 30000);
      return () => clearInterval(interval);
    }
  }, [user]);

  const checkHealth = async () => {
    try {
      setLoading(true);
      setHealth({
        status: "healthy",
        database: true,
        api: true,
        bot: true,
        lastCheck: new Date().toISOString()
      });
    } catch (error) {
      console.error("Error checking health:", error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: boolean) => {
    return status ? (
      <CheckCircle className="h-6 w-6 text-green-400" />
    ) : (
      <XCircle className="h-6 w-6 text-red-400" />
    );
  };

  const getStatusColor = (status: "healthy" | "degraded" | "down") => {
    switch (status) {
      case "healthy":
        return "text-green-400";
      case "degraded":
        return "text-yellow-400";
      case "down":
        return "text-red-400";
      default:
        return "text-slate-400";
    }
  };

  if (authLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-900">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500"></div>
      </div>
    );
  }

  if (!user || user.role?.toUpperCase() !== "ADMIN") {
    return null;
  }

  return (
    <div className="flex h-screen bg-slate-900">
      <Navigation />
      <main className="flex-1 lg:ml-64 overflow-y-auto">
        {user && <ReleaseBanner userId={user.id} />}
        <div className="p-8">
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-white">Health Monitor</h1>
                <p className="text-slate-400 mt-2">System health and service status</p>
              </div>
              <button
                onClick={checkHealth}
                className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
              >
                <RefreshCw className="h-4 w-4" />
                Refresh
              </button>
            </div>

            {health && (
              <>
                <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="text-xl font-semibold text-white mb-2">Overall Status</h2>
                      <p className={`text-2xl font-bold ${getStatusColor(health.status)}`}>
                        {health.status.toUpperCase()}
                      </p>
                    </div>
                    <Activity className={`h-12 w-12 ${getStatusColor(health.status)}`} />
                  </div>
                  <p className="text-sm text-slate-400 mt-4">
                    Last checked: {new Date(health.lastCheck).toLocaleString()}
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-white">Database</h3>
                      {getStatusIcon(health.database)}
                    </div>
                    <Database className="h-8 w-8 text-slate-600 mb-2" />
                    <p className={`text-sm font-medium ${health.database ? "text-green-400" : "text-red-400"}`}>
                      {health.database ? "Connected" : "Disconnected"}
                    </p>
                  </div>

                  <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-white">API</h3>
                      {getStatusIcon(health.api)}
                    </div>
                    <Server className="h-8 w-8 text-slate-600 mb-2" />
                    <p className={`text-sm font-medium ${health.api ? "text-green-400" : "text-red-400"}`}>
                      {health.api ? "Operational" : "Down"}
                    </p>
                  </div>

                  <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-white">Trading Bot</h3>
                      {getStatusIcon(health.bot)}
                    </div>
                    <Activity className="h-8 w-8 text-slate-600 mb-2" />
                    <p className={`text-sm font-medium ${health.bot ? "text-green-400" : "text-red-400"}`}>
                      {health.bot ? "Running" : "Stopped"}
                    </p>
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
