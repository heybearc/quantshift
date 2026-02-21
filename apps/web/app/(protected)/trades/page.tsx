"use client";

import { useState, useEffect } from "react";
import { Navigation } from "@/components/navigation";
import { ReleaseBanner } from "@/components/release-banner";
import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";
import { Search, Calendar, BarChart2, Bitcoin } from "lucide-react";

type BotFilter = 'all' | 'equity-bot' | 'crypto-bot';

interface Trade {
  id: string;
  botName: string;
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
  const [botFilter, setBotFilter] = useState<BotFilter>('all');

  useEffect(() => {
    if (!loading && !user) router.push("/login");
  }, [user, loading, router]);

  useEffect(() => {
    if (user) fetchTrades();
  }, [user]);

  const fetchTrades = async () => {
    try {
      const response = await fetch("/api/bot/trades?limit=100");
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

  const fmt = (v: number) => new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(v);
  const fmtPct = (v: number) => `${v >= 0 ? "+" : ""}${v.toFixed(2)}%`;
  const fmtDate = (ts: string) => new Date(ts).toLocaleString('en-US', { timeZone: 'America/New_York', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', hour12: true });

  const filteredTrades = trades.filter(t =>
    (botFilter === 'all' || t.botName === botFilter) &&
    t.symbol.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const equityCount = trades.filter(t => t.botName === 'equity-bot').length;
  const cryptoCount = trades.filter(t => t.botName === 'crypto-bot').length;

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center bg-slate-900">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500" />
    </div>
  );
  if (!user) return null;

  return (
    <div className="flex h-screen bg-slate-900">
      <Navigation />
      <main className="flex-1 lg:ml-64 overflow-y-auto">
        {user && <ReleaseBanner userId={user.id} />}
        <div className="p-8">
          <div className="space-y-6">

            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <h1 className="text-3xl font-bold text-white">Trades</h1>
                <p className="text-slate-400 mt-1">{filteredTrades.length} trades shown</p>
              </div>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search symbol..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-9 pr-4 py-2 bg-slate-800 border border-slate-700 text-white text-sm rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500"
                />
              </div>
            </div>

            {/* Bot filter tabs */}
            <div className="flex items-center gap-1 bg-slate-800/50 rounded-xl p-1 border border-slate-700 w-fit">
              {([
                { id: 'all' as BotFilter, label: `All Bots (${trades.length})`, icon: null },
                { id: 'equity-bot' as BotFilter, label: `Equity Bot (${equityCount})`, icon: <BarChart2 className="h-3.5 w-3.5" /> },
                { id: 'crypto-bot' as BotFilter, label: `Crypto Bot (${cryptoCount})`, icon: <Bitcoin className="h-3.5 w-3.5" /> },
              ]).map(({ id, label, icon }) => (
                <button
                  key={id}
                  onClick={() => setBotFilter(id)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    botFilter === id ? 'bg-cyan-600 text-white shadow' : 'text-slate-400 hover:text-white hover:bg-slate-700'
                  }`}
                >
                  {icon}{label}
                </button>
              ))}
            </div>

            {dataLoading ? (
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500" />
              </div>
            ) : filteredTrades.length === 0 ? (
              <div className="bg-slate-800/50 rounded-xl border border-slate-700 p-12 text-center">
                <Calendar className="mx-auto h-12 w-12 text-slate-600 mb-4" />
                <h3 className="text-lg font-medium text-white mb-2">No Trades Found</h3>
                <p className="text-slate-400">
                  {searchTerm ? "No trades match your search." : "Trades will appear here once the bots start trading."}
                </p>
              </div>
            ) : (
              <div className="bg-slate-800/50 rounded-xl border border-slate-700 overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-slate-900/50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Bot</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Symbol</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Side</th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">Qty</th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">Entry</th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">Exit</th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">P&L</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Status</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Exit Reason</th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">Entered (ET)</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-700/50">
                      {filteredTrades.map((trade) => (
                        <tr key={trade.id} className="hover:bg-slate-700/30 transition-colors">
                          <td className="px-4 py-3 whitespace-nowrap">
                            {trade.botName === 'equity-bot'
                              ? <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-blue-900/40 text-blue-300"><BarChart2 className="h-3 w-3" />Equity</span>
                              : <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-orange-900/40 text-orange-300"><Bitcoin className="h-3 w-3" />Crypto</span>
                            }
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm font-semibold text-white">{trade.symbol}</td>
                          <td className="px-4 py-3 whitespace-nowrap">
                            <span className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${trade.side === "BUY" ? "bg-green-900/30 text-green-400" : "bg-red-900/30 text-red-400"}`}>
                              {trade.side}
                            </span>
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm text-right text-slate-300">
                            {trade.quantity < 1 ? trade.quantity.toFixed(6) : trade.quantity.toFixed(2)}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm text-right text-white">{fmt(trade.entryPrice)}</td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm text-right text-white">
                            {trade.exitPrice ? fmt(trade.exitPrice) : <span className="text-slate-500">—</span>}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm text-right">
                            {trade.pnl !== undefined && trade.pnl !== null ? (
                              <div className="flex flex-col items-end">
                                <span className={`font-semibold ${trade.pnl >= 0 ? "text-green-400" : "text-red-400"}`}>{fmt(trade.pnl)}</span>
                                {trade.pnlPercent !== undefined && trade.pnlPercent !== null && (
                                  <span className="text-xs text-slate-500">{fmtPct(trade.pnlPercent)}</span>
                                )}
                              </div>
                            ) : <span className="text-slate-500">—</span>}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap">
                            <span className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${
                              trade.status === "CLOSED" ? "bg-slate-700 text-slate-300" : "bg-cyan-900/30 text-cyan-400"
                            }`}>
                              {trade.status}
                            </span>
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-xs text-slate-400">
                            {trade.exitReason
                              ? <span className={`${trade.exitReason === 'stop_loss' ? 'text-red-400' : trade.exitReason === 'take_profit' ? 'text-green-400' : 'text-slate-400'}`}>
                                  {trade.exitReason.replace('_', ' ')}
                                </span>
                              : <span className="text-slate-600">—</span>}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-xs text-right text-slate-400">
                            {fmtDate(trade.enteredAt)}
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
