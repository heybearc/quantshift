'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

interface StrategyPerformance {
  strategy: string;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  profit_factor: number;
  total_pnl: number;
}

export default function StrategiesPage() {
  const [strategies, setStrategies] = useState<StrategyPerformance[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStrategies = async () => {
      try {
        // TODO: Create /api/strategies endpoint
        // For now, show placeholder data
        setStrategies([
          {
            strategy: 'MA_Crossover',
            total_trades: 0,
            winning_trades: 0,
            losing_trades: 0,
            win_rate: 0,
            profit_factor: 0,
            total_pnl: 0
          },
          {
            strategy: 'Mean_Reversion',
            total_trades: 0,
            winning_trades: 0,
            losing_trades: 0,
            win_rate: 0,
            profit_factor: 0,
            total_pnl: 0
          },
          {
            strategy: 'Breakout',
            total_trades: 0,
            winning_trades: 0,
            losing_trades: 0,
            win_rate: 0,
            profit_factor: 0,
            total_pnl: 0
          }
        ]);
      } catch (error) {
        console.error('Error fetching strategies:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStrategies();
    const interval = setInterval(fetchStrategies, 10000);
    
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8 flex justify-between items-center">
          <div>
            <h1 className="text-4xl font-bold text-white mb-2">Strategy Performance</h1>
            <p className="text-slate-400">Compare performance across trading strategies</p>
          </div>
          <Link href="/" className="px-4 py-2 bg-slate-700 text-white rounded hover:bg-slate-600">
            ← Back to Dashboard
          </Link>
        </div>

        {loading ? (
          <div className="text-center text-white py-12">Loading strategies...</div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {strategies.map((strategy) => (
              <Card key={strategy.strategy} className="bg-slate-800 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-white text-xl">
                    {strategy.strategy.replace('_', ' ')}
                  </CardTitle>
                  <CardDescription className="text-slate-400">
                    {strategy.total_trades} total trades
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-slate-400 text-sm">Win Rate</span>
                        <span className="text-white font-semibold">
                          {strategy.win_rate > 0 ? `${strategy.win_rate.toFixed(1)}%` : 'N/A'}
                        </span>
                      </div>
                      {strategy.total_trades > 0 && (
                        <div className="w-full bg-slate-700 rounded-full h-2">
                          <div 
                            className="bg-green-500 h-2 rounded-full" 
                            style={{ width: `${strategy.win_rate}%` }}
                          />
                        </div>
                      )}
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-slate-400 text-sm">Winning</p>
                        <p className="text-green-400 font-semibold">{strategy.winning_trades}</p>
                      </div>
                      <div>
                        <p className="text-slate-400 text-sm">Losing</p>
                        <p className="text-red-400 font-semibold">{strategy.losing_trades}</p>
                      </div>
                    </div>

                    <div className="border-t border-slate-700 pt-4">
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-slate-400 text-sm">Profit Factor</span>
                        <span className="text-white font-semibold">
                          {strategy.profit_factor > 0 ? strategy.profit_factor.toFixed(2) : 'N/A'}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-slate-400 text-sm">Total P&L</span>
                        <span className={`font-semibold ${
                          strategy.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'
                        }`}>
                          {strategy.total_pnl !== 0 
                            ? `${strategy.total_pnl >= 0 ? '+' : ''}$${strategy.total_pnl.toFixed(2)}`
                            : '$0.00'
                          }
                        </span>
                      </div>
                    </div>

                    {strategy.total_trades === 0 && (
                      <div className="bg-slate-900 rounded p-3 text-center">
                        <p className="text-slate-500 text-sm">No trades yet</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        <Card className="mt-6 bg-slate-800 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white">Strategy Allocation</CardTitle>
            <CardDescription className="text-slate-400">
              Capital allocated to each strategy
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-white">MA Crossover</span>
                  <span className="text-slate-400">40%</span>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-3">
                  <div className="bg-blue-500 h-3 rounded-full" style={{ width: '40%' }} />
                </div>
              </div>
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-white">Mean Reversion</span>
                  <span className="text-slate-400">30%</span>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-3">
                  <div className="bg-purple-500 h-3 rounded-full" style={{ width: '30%' }} />
                </div>
              </div>
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-white">Breakout</span>
                  <span className="text-slate-400">30%</span>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-3">
                  <div className="bg-green-500 h-3 rounded-full" style={{ width: '30%' }} />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
