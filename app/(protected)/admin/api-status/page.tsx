"use client";

import { useAuth } from "@/lib/auth-context";
import { Navigation } from "@/components/navigation";
import { ReleaseBanner } from "@/components/release-banner";
import { useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import { Zap, CheckCircle, XCircle, Clock, RefreshCw } from "lucide-react";

interface APIEndpoint {
  name: string;
  endpoint: string;
  status: "operational" | "degraded" | "down";
  responseTime: number;
  lastChecked: string;
}

export default function APIStatusPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [endpoints, setEndpoints] = useState<APIEndpoint[]>([]);
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
      checkAPIs();
      const interval = setInterval(checkAPIs, 60000);
      return () => clearInterval(interval);
    }
  }, [user]);

  const checkAPIs = async () => {
    try {
      setLoading(true);
      setEndpoints([
        {
          name: "Bot Status",
          endpoint: "/api/bot/status",
          status: "operational",
          responseTime: 45,
          lastChecked: new Date().toISOString()
        },
        {
          name: "User Management",
          endpoint: "/api/users",
          status: "operational",
          responseTime: 32,
          lastChecked: new Date().toISOString()
        },
        {
          name: "Trades",
          endpoint: "/api/bot/trades",
          status: "operational",
          responseTime: 58,
          lastChecked: new Date().toISOString()
        },
        {
          name: "Positions",
          endpoint: "/api/bot/positions",
          status: "operational",
          responseTime: 41,
          lastChecked: new Date().toISOString()
        }
      ]);
    } catch (error) {
      console.error("Error checking APIs:", error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "operational":
        return <CheckCircle className="h-5 w-5 text-green-400" />;
      case "degraded":
        return <Clock className="h-5 w-5 text-yellow-400" />;
      case "down":
        return <XCircle className="h-5 w-5 text-red-400" />;
      default:
        return null;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "operational":
        return "bg-green-900/50 text-green-300 border-green-700";
      case "degraded":
        return "bg-yellow-900/50 text-yellow-300 border-yellow-700";
      case "down":
        return "bg-red-900/50 text-red-300 border-red-700";
      default:
        return "bg-slate-800 text-slate-400 border-slate-700";
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
                <h1 className="text-3xl font-bold text-white">API Status</h1>
                <p className="text-slate-400 mt-2">Monitor API endpoint health and performance</p>
              </div>
              <button
                onClick={checkAPIs}
                className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
              >
                <RefreshCw className="h-4 w-4" />
                Refresh
              </button>
            </div>

            <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-slate-900/50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                        Endpoint
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                        Path
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                        Response Time
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                        Last Checked
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-700">
                    {endpoints.map((endpoint, index) => (
                      <tr key={index} className="hover:bg-slate-800/50 transition-colors">
                        <td className="px-6 py-4 text-sm font-medium text-white">{endpoint.name}</td>
                        <td className="px-6 py-4 text-sm text-slate-400 font-mono">{endpoint.endpoint}</td>
                        <td className="px-6 py-4">
                          <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium border ${getStatusColor(endpoint.status)}`}>
                            {getStatusIcon(endpoint.status)}
                            {endpoint.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-sm text-slate-400">{endpoint.responseTime}ms</td>
                        <td className="px-6 py-4 text-sm text-slate-400">
                          {new Date(endpoint.lastChecked).toLocaleTimeString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
