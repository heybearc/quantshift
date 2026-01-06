"use client";

import { useState, useEffect } from "react";
import { Navigation } from "@/components/navigation";
import { ReleaseBanner } from "@/components/release-banner";
import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";
import { TrendingUp, TrendingDown, DollarSign, Activity } from "lucide-react";

interface Position {
  id: string;
  symbol: string;
  quantity: number;
  entryPrice: number;
  currentPrice: number;
  marketValue: number;
  costBasis: number;
  unrealizedPl: number;
  unrealizedPlPct: number;
  stopLoss?: number;
  takeProfit?: number;
  strategy: string;
  enteredAt: string;
}

export default function PositionsPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [positions, setPositions] = useState<Position[]>([]);
  const [dataLoading, setDataLoading] = useState(true);

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
  }, [user, loading, router]);

  useEffect(() => {
    if (user) {
      fetchPositions();
      const interval = setInterval(fetchPositions, 30000);
      return () => clearInterval(interval);
    }
  }, [user]);

  const fetchPositions = async () => {
    try {
      const response = await fetch("/api/bot/positions");
      if (response.ok) {
        const data = await response.json();
        setPositions(data.positions || []);
      }
    } catch (error) {
      console.error("Error fetching positions:", error);
    } finally {
      setDataLoading(false);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
  };

  const totalMarketValue = positions.reduce((sum, p) => sum + p.marketValue, 0);
  const totalCostBasis = positions.reduce((sum, p) => sum + p.costBasis, 0);
  const totalUnrealizedPl = positions.reduce((sum, p) => sum + p.unrealizedPl, 0);
  const totalUnrealizedPlPct = totalCostBasis > 0 ? (totalUnrealizedPl / totalCostBasis) * 100 : 0;

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
              <h1 className="text-3xl font-bold text-white">Current Positions</h1>
              <p className="text-slate-400 mt-2">{positions.length} active positions</p>
            </div>

            {dataLoading ? (
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500"></div>
              </div>
            ) : (
              <>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-sm font-medium text-slate-400">Total Market Value</h3>
                      <DollarSign className="h-5 w-5 text-cyan-500" />
                    </div>
                    <p className="text-2xl font-bold text-white">{formatCurrency(totalMarketValue)}</p>
                    <p className="text-sm text-slate-400 mt-1">Cost basis: {formatCurrency(totalCostBasis)}</p>
                  </div>

                  <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-sm font-medium text-slate-400">Unrealized P&L</h3>
                      {totalUnrealizedPl >= 0 ? (
                        <TrendingUp className="h-5 w-5 text-green-500" />
                      ) : (
                        <TrendingDown className="h-5 w-5 text-red-500" />
                      )}
                    </div>
                    <p className={`text-2xl font-bold ${totalUnrealizedPl >= 0 ? "text-green-500" : "text-red-500"}`}>
                      {formatCurrency(totalUnrealizedPl)}
                    </p>
                    <p className="text-sm text-slate-400 mt-1">{formatPercent(totalUnrealizedPlPct)}</p>
                  </div>

                  <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-sm font-medium text-slate-400">Active Positions</h3>
                      <Activity className="h-5 w-5 text-cyan-500" />
                    </div>
                    <p className="text-2xl font-bold text-white">{positions.length}</p>
                    <p className="text-sm text-slate-400 mt-1">Active trades</p>
                  </div>
                </div>

                <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 overflow-hidden">
                  {positions.length === 0 ? (
                    <div className="p-12 text-center">
                      <Activity className="mx-auto h-12 w-12 text-slate-600 mb-4" />
                      <h3 className="text-lg font-medium text-white mb-2">No Active Positions</h3>
                      <p className="text-slate-400">Positions will appear here once the bot starts trading.</p>
                    </div>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead className="bg-slate-900/50">
                          <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Symbol</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Strategy</th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">Quantity</th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">Entry Price</th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">Current Price</th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">Market Value</th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">Unrealized P&L</th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">Entered</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-700">
                          {positions.map((position) => (
                            <tr key={position.id} className="hover:bg-slate-700/30">
                              <td className="px-6 py-4 whitespace-nowrap">
                                <div className="flex items-center">
                                  <span className="text-sm font-medium text-white">{position.symbol}</span>
                                  {position.unrealizedPlPct >= 0 ? (
                                    <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-900/30 text-green-400">
                                      {formatPercent(position.unrealizedPlPct)}
                                    </span>
                                  ) : (
                                    <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-900/30 text-red-400">
                                      {formatPercent(position.unrealizedPlPct)}
                                    </span>
                                  )}
                                </div>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-400">{position.strategy}</td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-white">{position.quantity.toFixed(8)}</td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-white">{formatCurrency(position.entryPrice)}</td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-white">{formatCurrency(position.currentPrice)}</td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-white">{formatCurrency(position.marketValue)}</td>
                              <td className={`px-6 py-4 whitespace-nowrap text-sm text-right font-medium ${position.unrealizedPl >= 0 ? "text-green-500" : "text-red-500"}`}>
                                {formatCurrency(position.unrealizedPl)}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-slate-400">
                                {new Date(position.enteredAt).toLocaleDateString()}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
