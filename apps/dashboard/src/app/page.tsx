import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">QuantShift Trading Platform</h1>
          <p className="text-slate-400">Real-time monitoring and management for your trading bots</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Link href="/bots">
            <Card className="hover:shadow-lg transition-shadow cursor-pointer bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">Bot Status</CardTitle>
                <CardDescription className="text-slate-400">Monitor active bots and their health</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-green-400">2 Active</div>
                <p className="text-sm text-slate-400 mt-2">Equity • Crypto</p>
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
                <div className="text-3xl font-bold text-blue-400">0</div>
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
                <div className="text-3xl font-bold text-yellow-400">0</div>
                <p className="text-sm text-slate-400 mt-2">Closed trades</p>
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
                <div className="text-3xl font-bold text-emerald-400">--</div>
                <p className="text-sm text-slate-400 mt-2">Win rate • Sharpe • Drawdown</p>
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

        <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white">System Status</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Primary Bot (LXC 100)</span>
                  <span className="px-2 py-1 bg-green-500/20 text-green-400 rounded text-sm">Running</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Standby Bot (LXC 101)</span>
                  <span className="px-2 py-1 bg-green-500/20 text-green-400 rounded text-sm">Running</span>
                </div>
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
                  <span className="text-white font-semibold">$10,000.00</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Unrealized P&L</span>
                  <span className="text-green-400 font-semibold">$0.00</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Today's Trades</span>
                  <span className="text-white font-semibold">0</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Win Rate</span>
                  <span className="text-white font-semibold">--</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
