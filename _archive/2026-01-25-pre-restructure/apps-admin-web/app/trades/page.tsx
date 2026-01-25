'use client';

import { ProtectedRoute } from '@/components/protected-route';
import { LayoutWrapper } from '@/components/layout-wrapper';
import { useState, useEffect } from 'react';
import { Search, Filter, TrendingUp, TrendingDown, Calendar, DollarSign } from 'lucide-react';
import Link from 'next/link';

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
  const [trades, setTrades] = useState<Trade[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [symbolFilter, setSymbolFilter] = useState('');
  const [pagination, setPagination] = useState({ total: 0, limit: 50, offset: 0, hasMore: false });

  useEffect(() => {
    fetchTrades();
  }, [statusFilter, symbolFilter, pagination.offset]);

  const fetchTrades = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        limit: pagination.limit.toString(),
        offset: pagination.offset.toString(),
      });
      if (statusFilter) params.append('status', statusFilter);
      if (symbolFilter) params.append('symbol', symbolFilter);

      const response = await fetch(`/api/bot/trades?${params}`);
      if (response.ok) {
        const data = await response.json();
        setTrades(data.trades || []);
        setPagination(data.pagination);
      }
    } catch (error) {
      console.error('Error fetching trades:', error);
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

  const filteredTrades = trades.filter(trade => {
    const matchesSearch = !searchTerm || 
      trade.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
      trade.strategy.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesSearch;
  });

  const uniqueSymbols = Array.from(new Set(trades.map(t => t.symbol)));

  if (loading && trades.length === 0) {
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
                <h1 className="text-3xl font-bold text-gray-900">Trade History</h1>
                <p className="mt-1 text-gray-600">
                  {pagination.total} total trades
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

          {/* Search and Filters */}
          <div className="bg-white rounded-lg shadow p-4 mb-6">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search by symbol or strategy..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex gap-2">
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">All Status</option>
                  <option value="OPEN">Open</option>
                  <option value="CLOSED">Closed</option>
                  <option value="CANCELLED">Cancelled</option>
                </select>
                <select
                  value={symbolFilter}
                  onChange={(e) => setSymbolFilter(e.target.value)}
                  className="px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">All Symbols</option>
                  {uniqueSymbols.map(symbol => (
                    <option key={symbol} value={symbol}>{symbol}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Trades Table */}
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Symbol
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Side
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Quantity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Entry Price
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Exit Price
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    P&L
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredTrades.map((trade) => (
                  <tr key={trade.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="text-sm font-medium text-gray-900">{trade.symbol}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        trade.side === 'BUY' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {trade.side}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {trade.quantity}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatCurrency(trade.entryPrice)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {trade.exitPrice ? formatCurrency(trade.exitPrice) : '—'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {trade.pnl !== undefined ? (
                        <div>
                          <div className={`text-sm font-medium ${trade.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {formatCurrency(trade.pnl)}
                          </div>
                          {trade.pnlPercent !== undefined && (
                            <div className={`text-xs ${trade.pnlPercent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                              {formatPercent(trade.pnlPercent)}
                            </div>
                          )}
                        </div>
                      ) : (
                        <span className="text-sm text-gray-500">—</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        trade.status === 'CLOSED' ? 'bg-gray-100 text-gray-800' :
                        trade.status === 'OPEN' ? 'bg-blue-100 text-blue-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {trade.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <div>{formatDate(trade.enteredAt)}</div>
                      {trade.exitedAt && (
                        <div className="text-xs text-gray-400">Exit: {formatDate(trade.exitedAt)}</div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {filteredTrades.length === 0 && (
              <div className="text-center py-12">
                <TrendingUp className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No trades found</h3>
                <p className="mt-1 text-sm text-gray-500">
                  {searchTerm || statusFilter || symbolFilter
                    ? 'Try adjusting your search or filters'
                    : 'Trades will appear here once the bot starts trading'}
                </p>
              </div>
            )}
          </div>

          {/* Pagination */}
          {pagination.total > pagination.limit && (
            <div className="mt-6 flex items-center justify-between">
              <div className="text-sm text-gray-700">
                Showing {pagination.offset + 1} to {Math.min(pagination.offset + pagination.limit, pagination.total)} of {pagination.total} trades
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setPagination(prev => ({ ...prev, offset: Math.max(0, prev.offset - prev.limit) }))}
                  disabled={pagination.offset === 0}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPagination(prev => ({ ...prev, offset: prev.offset + prev.limit }))}
                  disabled={!pagination.hasMore}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
      </LayoutWrapper>
    </ProtectedRoute>
  );
}
