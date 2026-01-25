'use client';

import { ProtectedRoute } from '@/components/protected-route';
import { LayoutWrapper } from '@/components/layout-wrapper';
import { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, DollarSign, Activity } from 'lucide-react';
import Link from 'next/link';

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
  const [positions, setPositions] = useState<Position[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPositions();
    // Refresh every 30 seconds
    const interval = setInterval(fetchPositions, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchPositions = async () => {
    try {
      const response = await fetch('/api/bot/positions');
      if (response.ok) {
        const data = await response.json();
        setPositions(data.positions || []);
      }
    } catch (error) {
      console.error('Error fetching positions:', error);
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

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const totalUnrealizedPl = positions.reduce((sum, pos) => sum + pos.unrealizedPl, 0);
  const totalMarketValue = positions.reduce((sum, pos) => sum + pos.marketValue, 0);
  const totalCostBasis = positions.reduce((sum, pos) => sum + pos.costBasis, 0);

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
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Header */}
          <div className="mb-6">
            <div className="flex justify-between items-center mb-4">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Current Positions</h1>
                <p className="mt-1 text-gray-600">
                  {positions.length} open position{positions.length !== 1 ? 's' : ''}
                </p>
              </div>
              <Link
                href="/dashboard"
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                ← Back to Dashboard
              </Link>
            </div>
          </div>

          {/* Summary Cards */}
          {positions.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-medium text-gray-600">Total Market Value</h3>
                  <DollarSign className="h-5 w-5 text-blue-600" />
                </div>
                <p className="text-2xl font-bold text-gray-900">{formatCurrency(totalMarketValue)}</p>
                <p className="text-sm text-gray-600 mt-1">Cost basis: {formatCurrency(totalCostBasis)}</p>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-medium text-gray-600">Unrealized P&L</h3>
                  {totalUnrealizedPl >= 0 ? (
                    <TrendingUp className="h-5 w-5 text-green-600" />
                  ) : (
                    <TrendingDown className="h-5 w-5 text-red-600" />
                  )}
                </div>
                <p className={`text-2xl font-bold ${totalUnrealizedPl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatCurrency(totalUnrealizedPl)}
                </p>
                <p className={`text-sm mt-1 ${totalUnrealizedPl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatPercent((totalUnrealizedPl / totalCostBasis) * 100)}
                </p>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-medium text-gray-600">Open Positions</h3>
                  <Activity className="h-5 w-5 text-purple-600" />
                </div>
                <p className="text-2xl font-bold text-gray-900">{positions.length}</p>
                <p className="text-sm text-gray-600 mt-1">Active trades</p>
              </div>
            </div>
          )}

          {/* Positions Grid */}
          {positions.length > 0 ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {positions.map((position) => (
                <div key={position.id} className="bg-white rounded-lg shadow p-6">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="text-xl font-bold text-gray-900">{position.symbol}</h3>
                      <p className="text-sm text-gray-600">{position.strategy}</p>
                    </div>
                    <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                      position.unrealizedPl >= 0 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {formatPercent(position.unrealizedPlPct)}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div>
                      <p className="text-xs text-gray-600">Quantity</p>
                      <p className="text-lg font-semibold text-gray-900">{position.quantity}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-600">Entry Price</p>
                      <p className="text-lg font-semibold text-gray-900">{formatCurrency(position.entryPrice)}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-600">Current Price</p>
                      <p className="text-lg font-semibold text-gray-900">{formatCurrency(position.currentPrice)}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-600">Market Value</p>
                      <p className="text-lg font-semibold text-gray-900">{formatCurrency(position.marketValue)}</p>
                    </div>
                  </div>

                  <div className="border-t border-gray-200 pt-4">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm text-gray-600">Unrealized P&L</span>
                      <span className={`text-lg font-bold ${
                        position.unrealizedPl >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {formatCurrency(position.unrealizedPl)}
                      </span>
                    </div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm text-gray-600">Cost Basis</span>
                      <span className="text-sm text-gray-900">{formatCurrency(position.costBasis)}</span>
                    </div>
                    {position.stopLoss && (
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm text-gray-600">Stop Loss</span>
                        <span className="text-sm text-red-600">{formatCurrency(position.stopLoss)}</span>
                      </div>
                    )}
                    {position.takeProfit && (
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm text-gray-600">Take Profit</span>
                        <span className="text-sm text-green-600">{formatCurrency(position.takeProfit)}</span>
                      </div>
                    )}
                    <div className="flex justify-between items-center mt-3 pt-3 border-t border-gray-100">
                      <span className="text-xs text-gray-500">Entered</span>
                      <span className="text-xs text-gray-500">{formatDate(position.enteredAt)}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow p-12 text-center">
              <Activity className="mx-auto h-16 w-16 text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Open Positions</h3>
              <p className="text-gray-600 mb-6">
                The bot currently has no active trades. Positions will appear here when the bot enters new trades.
              </p>
              <Link
                href="/trades"
                className="inline-flex items-center px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-700"
              >
                View Trade History →
              </Link>
            </div>
          )}
        </div>
      </div>
      </LayoutWrapper>
    </ProtectedRoute>
  );
}
