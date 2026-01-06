"use client";

import { useState, useEffect } from "react";
import { Navigation } from "@/components/navigation";
import { ReleaseBanner } from "@/components/release-banner";
import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";
import { Search, TrendingUp, TrendingDown, Calendar, DollarSign } from "lucide-react";

interface Trade {
  id: string;
  symbol: string;
  side: string;
  quantity: number;
  entryPrice: number;
  exitPrice?: number;
  stopLoss?: number;
  takeProfit?: number;
  status: string;
  pnl?: number;
  pnlPercent?: number;
  strategy: string;
  signalType?: string;
  entryReason?: string;
  exitReason?: string;
  enteredAt: string;
  exitedAt?: string;
}

export default function TradesPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [trades, setTrades] = useState<Trade[]>([]);
  const [dataLoading, setDataLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
  }, [user, loading, router]);

  useEffect(() => {
    if (user) {
      fetchTrades();
    }
  }, [user]);

  const fetchTrades = async () => {
    try {
      const response = await fetch("/api/bot/trades?limit=50");
      if (response.ok) {
        const data = await response.json();
        setTrades(data.trades || []);
      }
    } catch (error) {
      console.error("Error fetching trades:", error);
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

  const filteredTrades = trades.filter((trade) =>
    trade.symbol.toLowerCase().includes(searchTerm.toLowerCase())
  );

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
            <div className="flex justify-between items-center">
              <div>
                <h1 className="text-3xl font-bold text-white">Trade History</h1>
                <p className="text-slate-400 mt-2">{filteredTrades.length} total trades</p>
              </div>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search by symbol..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-4 py-2 bg-slate-800 border border-slate-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500"
                />
              </div>
            </div>

            {dataLoading ? (
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500"></div>
              </div>
            ) : filteredTrades.length === 0 ? (
              <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-12 text-center">
                <Calendar className="mx-auto h-12 w-12 text-slate-600 mb-4" />
                <h3 className="text-lg font-medium text-white mb-2">No Trades Found</h3>
                <p className="text-slate-400">
                  {searchTerm ? "No trades match your search." : "Trades will appear here once the bot starts trading."}
                </p>
              </div>
            ) : (
              <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-slate-900/50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Symbol</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Side</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Strategy</th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">Quantity</th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">Entry Price</th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">Exit Price</th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">P&L</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Status</th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">Date</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-700">
                      {filteredTrades.map((trade) => (
                        <tr key={trade.id} className="hover:bg-slate-700/30">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="text-sm font-medium text-white">{trade.symbol}</span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                              trade.side === "BUY" ? "bg-green-900/30 text-green-400" : "bg-red-900/30 text-red-400"
                            }`}>
                              {trade.side}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-400">{trade.strategy}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-white">{trade.quantity.toFixed(8)}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-white">{formatCurrency(trade.entryPrice)}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-white">
                            {trade.exitPrice ? formatCurrency(trade.exitPrice) : "-"}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                            {trade.pnl !== undefined ? (
                              <div className="flex flex-col items-end">
                                <span className={`font-medium ${trade.pnl >= 0 ? "text-green-500" : "text-red-500"}`}>
                                  {formatCurrency(trade.pnl)}
                                </span>
                                {trade.pnlPercent !== undefined && (
                                  <span className="text-xs text-slate-400">{formatPercent(trade.pnlPercent)}</span>
                                )}
                              </div>
                            ) : (
                              <span className="text-slate-400">-</span>
                            )}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                              trade.status === "CLOSED" ? "bg-slate-700 text-slate-300" : "bg-cyan-900/30 text-cyan-400"
                            }`}>
                              {trade.status}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-slate-400">
                            {new Date(trade.enteredAt).toLocaleDateString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
