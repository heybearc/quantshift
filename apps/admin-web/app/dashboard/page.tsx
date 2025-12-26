"use client";

import { ProtectedRoute } from '@/components/protected-route';
import { LayoutWrapper } from '@/components/layout-wrapper';
import { useAuth } from '@/lib/auth-context';
import { useState, useEffect } from 'react';
import Link from 'next/link';
import { 
  TrendingUp, 
  DollarSign, 
  Activity, 
  BarChart3,
  Settings,
  Mail,
  Users,
  PlayCircle,
  PauseCircle,
  AlertCircle
} from 'lucide-react';

interface BotStatus {
  status: string;
  lastHeartbeat: string;
  accountEquity: number;
  accountCash: number;
  buyingPower: number;
  portfolioValue: number;
  unrealizedPl: number;
  realizedPl: number;
  positionsCount: number;
  tradesCount: number;
  errorMessage?: string;
}

interface Trade {
  id: string;
  symbol: string;
  side: string;
  quantity: number;
  entryPrice: number;
  exitPrice?: number;
  status: string;
  pnl?: number;
  pnlPercent?: number;
  enteredAt: string;
  exitedAt?: string;
}

interface Position {
  id: string;
  symbol: string;
  quantity: number;
  entryPrice: number;
  currentPrice: number;
  unrealizedPl: number;
  unrealizedPlPct: number;
}

export default function DashboardPage() {
  const { user, logout } = useAuth();
  const [botStatus, setBotStatus] = useState<BotStatus | null>(null);
  const [recentTrades, setRecentTrades] = useState<Trade[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
    // Refresh every 30 seconds
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [statusRes, tradesRes, positionsRes] = await Promise.all([
        fetch('/api/bot/status'),
        fetch('/api/bot/trades?limit=5'),
        fetch('/api/bot/positions'),
      ]);

      if (statusRes.ok) {
        const status = await statusRes.json();
        setBotStatus(status);
      }

      if (tradesRes.ok) {
        const tradesData = await tradesRes.json();
        setRecentTrades(tradesData.trades || []);
      }

      if (positionsRes.ok) {
        const positionsData = await positionsRes.json();
        setPositions(positionsData.positions || []);
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'RUNNING':
        return 'text-green-600 bg-green-50';
      case 'STOPPED':
        return 'text-gray-600 bg-gray-50';
      case 'ERROR':
      case 'STALE':
        return 'text-red-600 bg-red-50';
      default:
        return 'text-yellow-600 bg-yellow-50';
    }
  };

  if (loading) {
    return (
      <ProtectedRoute>
        <LayoutWrapper>
          <div className="min-h-screen flex items-center justify-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        </LayoutWrapper>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute>
      <LayoutWrapper>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Bot Status Alert */}
          {botStatus && botStatus.status !== 'RUNNING' && (
            <div className={`mb-6 p-4 rounded-lg flex items-center gap-3 ${
              botStatus.status === 'ERROR' || botStatus.status === 'STALE' 
                ? 'bg-red-50 border border-red-200' 
                : 'bg-yellow-50 border border-yellow-200'
            }`}>
              <AlertCircle className={`h-5 w-5 ${
                botStatus.status === 'ERROR' || botStatus.status === 'STALE' 
                  ? 'text-red-600' 
                  : 'text-yellow-600'
              }`} />
              <div>
                <p className="font-medium text-gray-900">
                  Bot Status: {botStatus.status}
                </p>
                {botStatus.errorMessage && (
                  <p className="text-sm text-gray-600">{botStatus.errorMessage}</p>
                )}
              </div>
            </div>
          )}

          {/* Stats Overview */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {/* Bot Status Card */}
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-medium text-gray-600">Bot Status</h3>
                {botStatus?.status === 'RUNNING' ? (
                  <Activity className="h-5 w-5 text-green-600" />
                ) : (
                  <PauseCircle className="h-5 w-5 text-gray-600" />
                )}
              </div>
              <p className={`text-2xl font-bold mb-2 ${getStatusColor(botStatus?.status || 'UNKNOWN')}`}>
                {botStatus?.status || 'Unknown'}
              </p>
              <p className="text-sm text-gray-600">Paper Trading Mode</p>
            </div>

            {/* Account Balance Card */}
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-medium text-gray-600">Account Equity</h3>
                <DollarSign className="h-5 w-5 text-blue-600" />
              </div>
              <p className="text-2xl font-bold text-gray-900 mb-2">
                {botStatus ? formatCurrency(botStatus.accountEquity) : '$0.00'}
              </p>
              <p className={`text-sm ${botStatus && botStatus.unrealizedPl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {botStatus ? formatCurrency(botStatus.unrealizedPl) : '$0.00'} unrealized
              </p>
            </div>

            {/* Open Positions Card */}
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-medium text-gray-600">Open Positions</h3>
                <TrendingUp className="h-5 w-5 text-purple-600" />
              </div>
              <p className="text-2xl font-bold text-gray-900 mb-2">
                {botStatus?.positionsCount || 0}
              </p>
              <p className="text-sm text-gray-600">
                {positions.length > 0 ? `${positions.length} active` : 'No active trades'}
              </p>
            </div>

            {/* Total Trades Card */}
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-medium text-gray-600">Total Trades</h3>
                <BarChart3 className="h-5 w-5 text-orange-600" />
              </div>
              <p className="text-2xl font-bold text-gray-900 mb-2">
                {botStatus?.tradesCount || 0}
              </p>
              <p className={`text-sm ${botStatus && botStatus.realizedPl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {botStatus ? formatCurrency(botStatus.realizedPl) : '$0.00'} realized
              </p>
            </div>
          </div>

          {/* Recent Trades & Positions */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            {/* Recent Trades */}
            <div className="bg-white rounded-lg shadow">
              <div className="p-6 border-b border-gray-200">
                <div className="flex justify-between items-center">
                  <h3 className="text-lg font-semibold text-gray-900">Recent Trades</h3>
                  <Link href="/trades" className="text-sm text-blue-600 hover:text-blue-700">
                    View All →
                  </Link>
                </div>
              </div>
              <div className="p-6">
                {recentTrades.length > 0 ? (
                  <div className="space-y-4">
                    {recentTrades.map((trade) => (
                      <div key={trade.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div>
                          <p className="font-medium text-gray-900">{trade.symbol}</p>
                          <p className="text-sm text-gray-600">
                            {trade.side} {trade.quantity} @ {formatCurrency(trade.entryPrice)}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className={`font-medium ${trade.pnl && trade.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {trade.pnl ? formatCurrency(trade.pnl) : '—'}
                          </p>
                          <p className="text-xs text-gray-500">{trade.status}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-center text-gray-500 py-8">No trades yet</p>
                )}
              </div>
            </div>

            {/* Current Positions */}
            <div className="bg-white rounded-lg shadow">
              <div className="p-6 border-b border-gray-200">
                <div className="flex justify-between items-center">
                  <h3 className="text-lg font-semibold text-gray-900">Current Positions</h3>
                  <Link href="/positions" className="text-sm text-blue-600 hover:text-blue-700">
                    View All →
                  </Link>
                </div>
              </div>
              <div className="p-6">
                {positions.length > 0 ? (
                  <div className="space-y-4">
                    {positions.map((position) => (
                      <div key={position.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div>
                          <p className="font-medium text-gray-900">{position.symbol}</p>
                          <p className="text-sm text-gray-600">
                            {position.quantity} @ {formatCurrency(position.entryPrice)}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className={`font-medium ${position.unrealizedPl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {formatCurrency(position.unrealizedPl)}
                          </p>
                          <p className="text-xs text-gray-500">
                            {formatPercent(position.unrealizedPlPct)}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-center text-gray-500 py-8">No open positions</p>
                )}
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Link href="/trades" className="px-4 py-3 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors text-center">
                View Trades
              </Link>
              <Link href="/performance" className="px-4 py-3 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors text-center">
                Performance
              </Link>
              <Link href="/email" className="px-4 py-3 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors text-center">
                Email Settings
              </Link>
              {user?.role === 'ADMIN' && (
                <Link href="/users" className="px-4 py-3 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors text-center">
                  User Management
                </Link>
              )}
            </div>
          </div>
        </main>
      </LayoutWrapper>
    </ProtectedRoute>
  );
}
