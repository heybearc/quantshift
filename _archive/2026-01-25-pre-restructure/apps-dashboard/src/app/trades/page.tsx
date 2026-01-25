'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

interface Trade {
  id: string;
  symbol: string;
  action: string;
  quantity: number;
  price: number;
  pnl?: number;
  pnl_pct?: number;
  timestamp: string;
  bot_name?: string;
  strategy?: string;
}

export default function TradesPage() {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTrades = async () => {
      try {
        const res = await fetch('/api/trades?limit=50');
        const data = await res.json();
        setTrades(data.trades || []);
      } catch (error) {
        console.error('Error fetching trades:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchTrades();
    const interval = setInterval(fetchTrades, 10000); // Refresh every 10 seconds
    
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8 flex justify-between items-center">
          <div>
            <h1 className="text-4xl font-bold text-white mb-2">Trade History</h1>
            <p className="text-slate-400">View past trades and performance</p>
          </div>
          <Link href="/" className="px-4 py-2 bg-slate-700 text-white rounded hover:bg-slate-600">
            ← Back to Dashboard
          </Link>
        </div>

        {loading ? (
          <div className="text-center text-white py-12">Loading trades...</div>
        ) : trades.length === 0 ? (
          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="py-12 text-center">
              <p className="text-slate-400 text-lg">No trades yet</p>
              <p className="text-slate-500 text-sm mt-2">Trade history will appear here once bots start trading</p>
            </CardContent>
          </Card>
        ) : (
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white">Recent Trades</CardTitle>
              <CardDescription className="text-slate-400">Last 50 trades</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-slate-700">
                      <th className="text-left text-slate-400 py-3 px-4">Time</th>
                      <th className="text-left text-slate-400 py-3 px-4">Symbol</th>
                      <th className="text-left text-slate-400 py-3 px-4">Action</th>
                      <th className="text-right text-slate-400 py-3 px-4">Quantity</th>
                      <th className="text-right text-slate-400 py-3 px-4">Price</th>
                      <th className="text-right text-slate-400 py-3 px-4">P&L</th>
                      <th className="text-left text-slate-400 py-3 px-4">Bot</th>
                    </tr>
                  </thead>
                  <tbody>
                    {trades.map((trade) => (
                      <tr key={trade.id} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                        <td className="text-slate-300 py-3 px-4 text-sm">
                          {new Date(trade.timestamp).toLocaleString()}
                        </td>
                        <td className="text-white font-semibold py-3 px-4">{trade.symbol}</td>
                        <td className="py-3 px-4">
                          <span className={`px-2 py-1 rounded text-xs font-semibold ${
                            trade.action === 'BUY' 
                              ? 'bg-blue-500/20 text-blue-400' 
                              : 'bg-orange-500/20 text-orange-400'
                          }`}>
                            {trade.action}
                          </span>
                        </td>
                        <td className="text-white text-right py-3 px-4">{trade.quantity}</td>
                        <td className="text-white text-right py-3 px-4">${trade.price.toFixed(2)}</td>
                        <td className="text-right py-3 px-4">
                          {trade.pnl !== undefined ? (
                            <span className={`font-semibold ${
                              trade.pnl >= 0 ? 'text-green-400' : 'text-red-400'
                            }`}>
                              {trade.pnl >= 0 ? '+' : ''}${trade.pnl.toFixed(2)}
                              {trade.pnl_pct !== undefined && (
                                <span className="text-xs ml-1">
                                  ({trade.pnl_pct >= 0 ? '+' : ''}{trade.pnl_pct.toFixed(1)}%)
                                </span>
                              )}
                            </span>
                          ) : (
                            <span className="text-slate-500">-</span>
                          )}
                        </td>
                        <td className="text-slate-400 py-3 px-4 text-sm">
                          {trade.bot_name || 'N/A'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
