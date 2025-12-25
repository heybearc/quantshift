'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

interface BotData {
  name: string;
  status: string;
  positions: number;
  heartbeat: string | null;
}

interface Stats {
  totalPositions: number;
  unrealizedPnl: number;
  todayTrades: number;
  winRate: number;
  accountBalance: number;
}

export default function Home() {
  const [bots, setBots] = useState<BotData[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch bots data
        const botsRes = await fetch('/api/bots');
        const botsData = await botsRes.json();
        setBots(botsData.bots || []);
        
        // Fetch stats data separately with error handling
        try {
          const statsRes = await fetch('/api/stats');
          if (statsRes.ok) {
            const statsData = await statsRes.json();
            if (!statsData.error) {
              setStats(statsData);
            }
          }
        } catch (statsError) {
          console.error('Error fetching stats:', statsError);
          // Keep existing stats or use defaults
        }
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 5000); // Refresh every 5 seconds
    
    return () => clearInterval(interval);
  }, []);
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8 flex items-center gap-4">
          <img src="/logo.svg" alt="QuantShift Logo" className="w-16 h-16" />
          <div>
            <h1 className="text-4xl font-bold text-white mb-2">QuantShift Trading Platform</h1>
            <p className="text-slate-400">Real-time monitoring and management for your trading bots</p>
          </div>
        </div>

        {loading ? (
          <div className="text-center text-white py-12">Loading...</div>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <Link href="/bots">
                <Card className="hover:shadow-lg transition-shadow cursor-pointer bg-slate-800 border-slate-700">
                  <CardHeader>
                    <CardTitle className="text-white">Bot Status</CardTitle>
                    <CardDescription className="text-slate-400">Monitor active bots and their health</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold text-green-400">
                      {bots.filter(b => b.status === 'running').length} Active
                    </div>
                    <p className="text-sm text-slate-400 mt-2">
                      {bots.map(b => b.name.replace('-bot', '')).join(' • ')}
                    </p>
                  </CardContent>
                </Card>
              </Link>

              <Link href="/positions">
                <Card className="hover:shadow-lg transition-shadow cursor-pointer bg-slate-800 border-slate-700">
                  <CardHeader>
                    <CardTitle className="text-white">Open Positions</CardTitle>
                    <CardDescription className="text-slate-400">View and manage current positions</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold text-blue-400">
                      {stats?.totalPositions || 0}
                    </div>
                    <p className="text-sm text-slate-400 mt-2">Paper trading active</p>
                  </CardContent>
                </Card>
              </Link>

              <Link href="/strategies">
                <Card className="hover:shadow-lg transition-shadow cursor-pointer bg-slate-800 border-slate-700">
                  <CardHeader>
                    <CardTitle className="text-white">Strategies</CardTitle>
                    <CardDescription className="text-slate-400">Performance by strategy</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold text-purple-400">3</div>
                    <p className="text-sm text-slate-400 mt-2">MA • Mean Rev • Breakout</p>
                  </CardContent>
                </Card>
              </Link>

              <Link href="/trades">
                <Card className="hover:shadow-lg transition-shadow cursor-pointer bg-slate-800 border-slate-700">
                  <CardHeader>
                    <CardTitle className="text-white">Trade History</CardTitle>
                    <CardDescription className="text-slate-400">View past trades and performance</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold text-yellow-400">
                      {stats?.todayTrades || 0}
                    </div>
                    <p className="text-sm text-slate-400 mt-2">Today's trades</p>
                  </CardContent>
                </Card>
              </Link>

              <Link href="/analytics">
                <Card className="hover:shadow-lg transition-shadow cursor-pointer bg-slate-800 border-slate-700">
                  <CardHeader>
                    <CardTitle className="text-white">Analytics</CardTitle>
                    <CardDescription className="text-slate-400">Performance metrics and charts</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold text-emerald-400">
                      {stats?.winRate ? `${stats.winRate.toFixed(1)}%` : '--'}
                    </div>
                    <p className="text-sm text-slate-400 mt-2">Win rate</p>
                  </CardContent>
                </Card>
              </Link>

              <Link href="/settings">
                <Card className="hover:shadow-lg transition-shadow cursor-pointer bg-slate-800 border-slate-700">
                  <CardHeader>
                    <CardTitle className="text-white">Settings</CardTitle>
                    <CardDescription className="text-slate-400">Configure bots and strategies</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold text-orange-400">⚙️</div>
                    <p className="text-sm text-slate-400 mt-2">API keys • Allocations • Limits</p>
                  </CardContent>
                </Card>
              </Link>
            </div>
          </>
        )}

        <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white">System Status</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {bots.map((bot) => (
                  <div key={bot.name} className="flex justify-between items-center">
                    <span className="text-slate-400">{bot.name}</span>
                    <span className={`px-2 py-1 rounded text-sm ${
                      bot.status === 'running' 
                        ? 'bg-green-500/20 text-green-400' 
                        : 'bg-red-500/20 text-red-400'
                    }`}>
                      {bot.status}
                    </span>
                  </div>
                ))}
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Redis State</span>
                  <span className="px-2 py-1 bg-green-500/20 text-green-400 rounded text-sm">Connected</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Database</span>
                  <span className="px-2 py-1 bg-green-500/20 text-green-400 rounded text-sm">Connected</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white">Quick Stats</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Account Balance</span>
                  <span className="text-white font-semibold">
                    ${stats?.accountBalance.toFixed(2) || '10,000.00'}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Unrealized P&L</span>
                  <span className={`font-semibold ${
                    (stats?.unrealizedPnl || 0) >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    ${stats?.unrealizedPnl.toFixed(2) || '0.00'}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Today's Trades</span>
                  <span className="text-white font-semibold">{stats?.todayTrades || 0}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Win Rate</span>
                  <span className="text-white font-semibold">
                    {stats?.winRate ? `${stats.winRate.toFixed(1)}%` : '--'}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
