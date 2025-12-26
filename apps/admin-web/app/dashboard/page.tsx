"use client";

import { ProtectedRoute } from '@/components/protected-route';
import { useAuth } from '@/lib/auth-context';

export default function DashboardPage() {
  const { user, logout } = useAuth();

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white shadow">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">QuantShift Admin</h1>
              <p className="text-sm text-gray-600">Trading Bot Control Center</p>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900">{user?.full_name || user?.email}</p>
                <p className="text-xs text-gray-500 capitalize">{user?.role}</p>
              </div>
              <button
                onClick={logout}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Bot Status Card */}
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Bot Status</h3>
                <span className="flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-3 w-3 rounded-full bg-green-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
                </span>
              </div>
              <p className="text-3xl font-bold text-green-600 mb-2">Running</p>
              <p className="text-sm text-gray-600">Paper Trading Mode</p>
            </div>

            {/* Account Balance Card */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Account Balance</h3>
              <p className="text-3xl font-bold text-gray-900 mb-2">$1,000.00</p>
              <p className="text-sm text-green-600">+$0.00 (0.00%)</p>
            </div>

            {/* Open Positions Card */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Open Positions</h3>
              <p className="text-3xl font-bold text-gray-900 mb-2">0</p>
              <p className="text-sm text-gray-600">No active trades</p>
            </div>

            {/* Today's Performance Card */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Today's Performance</h3>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Trades:</span>
                  <span className="text-sm font-medium text-gray-900">0</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">P&L:</span>
                  <span className="text-sm font-medium text-gray-900">$0.00</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Win Rate:</span>
                  <span className="text-sm font-medium text-gray-900">N/A</span>
                </div>
              </div>
            </div>

            {/* Strategy Info Card */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Strategy</h3>
              <p className="text-lg font-medium text-gray-900 mb-2">MA Crossover (5/20)</p>
              <p className="text-sm text-gray-600">Risk: 1% per trade</p>
            </div>

            {/* Email Notifications Card */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Notifications</h3>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="flex h-2 w-2 rounded-full bg-green-500"></span>
                  <span className="text-sm text-gray-600">Email alerts enabled</span>
                </div>
                <p className="text-xs text-gray-500 mt-2">{user?.email}</p>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="mt-8 bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <button className="px-4 py-3 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors">
                View Trades
              </button>
              <button className="px-4 py-3 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors">
                Email Settings
              </button>
              <button className="px-4 py-3 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors">
                Bot Logs
              </button>
              <button className="px-4 py-3 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors">
                Performance
              </button>
            </div>
          </div>

          {/* Welcome Message */}
          <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-blue-900 mb-2">
              🎉 Welcome to QuantShift Admin!
            </h3>
            <p className="text-sm text-blue-800">
              Your trading bot is currently running in paper trading mode. The bot will validate the MA 5/20 strategy over the next 30 days before going live.
            </p>
            <div className="mt-4 flex gap-4">
              <div className="text-sm">
                <span className="font-medium text-blue-900">Started:</span>
                <span className="text-blue-800 ml-2">December 26, 2025</span>
              </div>
              <div className="text-sm">
                <span className="font-medium text-blue-900">Expected Completion:</span>
                <span className="text-blue-800 ml-2">~January 26, 2026</span>
              </div>
            </div>
          </div>
        </main>
      </div>
    </ProtectedRoute>
  );
}
