'use client';

import { ProtectedRoute } from '@/components/protected-route';
import { useAuth } from '@/lib/auth-context';
import { useState, useEffect } from 'react';
import { Settings, Save, PlayCircle, PauseCircle, AlertCircle, CheckCircle } from 'lucide-react';
import Link from 'next/link';

interface BotConfig {
  name: string;
  strategy: string;
  symbols: string[];
  enabled: boolean;
  paperTrading: boolean;
  riskPerTrade: number;
  maxPositionSize: number;
  maxPortfolioHeat: number;
  simulatedCapital?: number;
}

export default function SettingsPage() {
  const { user } = useAuth();
  const [config, setConfig] = useState<BotConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [symbolInput, setSymbolInput] = useState('');

  useEffect(() => {
    if (user?.role !== 'ADMIN') {
      window.location.href = '/dashboard';
      return;
    }
    fetchConfig();
  }, [user]);

  const fetchConfig = async () => {
    try {
      const response = await fetch('/api/bot/config');
      if (response.ok) {
        const data = await response.json();
        setConfig(data);
      }
    } catch (error) {
      console.error('Error fetching config:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!config) return;
    
    setSaving(true);
    setMessage(null);
    try {
      const response = await fetch('/api/bot/config', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });

      if (response.ok) {
        setMessage({ type: 'success', text: 'Bot configuration saved successfully!' });
      } else {
        throw new Error('Failed to save configuration');
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to save bot configuration. Please try again.' });
    } finally {
      setSaving(false);
    }
  };

  const handleAddSymbol = () => {
    if (!config || !symbolInput.trim()) return;
    const symbol = symbolInput.trim().toUpperCase();
    if (!config.symbols.includes(symbol)) {
      setConfig({ ...config, symbols: [...config.symbols, symbol] });
    }
    setSymbolInput('');
  };

  const handleRemoveSymbol = (symbol: string) => {
    if (!config) return;
    setConfig({ ...config, symbols: config.symbols.filter(s => s !== symbol) });
  };

  if (user?.role !== 'ADMIN') {
    return null;
  }

  if (loading) {
    return (
      <ProtectedRoute>
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </ProtectedRoute>
    );
  }

  if (!config) {
    return (
      <ProtectedRoute>
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="text-center">
            <AlertCircle className="mx-auto h-12 w-12 text-yellow-600 mb-4" />
            <h3 className="text-lg font-medium text-gray-900">No Configuration Found</h3>
            <p className="text-gray-600 mt-2">Bot configuration could not be loaded.</p>
          </div>
        </div>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Header */}
          <div className="mb-6">
            <div className="flex justify-between items-center mb-4">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Bot Settings</h1>
                <p className="mt-1 text-gray-600">
                  Configure trading bot parameters and risk management
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

          {/* Message Alert */}
          {message && (
            <div className={`mb-6 p-4 rounded-lg flex items-center gap-3 ${
              message.type === 'success' 
                ? 'bg-green-50 border border-green-200' 
                : 'bg-red-50 border border-red-200'
            }`}>
              {message.type === 'success' ? (
                <CheckCircle className="h-5 w-5 text-green-600" />
              ) : (
                <AlertCircle className="h-5 w-5 text-red-600" />
              )}
              <p className={`text-sm ${message.type === 'success' ? 'text-green-800' : 'text-red-800'}`}>
                {message.text}
              </p>
            </div>
          )}

          {/* Bot Status */}
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {config.enabled ? (
                  <PlayCircle className="h-8 w-8 text-green-600" />
                ) : (
                  <PauseCircle className="h-8 w-8 text-gray-600" />
                )}
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">Bot Status</h2>
                  <p className={`text-sm ${config.enabled ? 'text-green-600' : 'text-gray-600'}`}>
                    {config.enabled ? 'Enabled' : 'Disabled'}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setConfig({ ...config, enabled: !config.enabled })}
                className={`px-4 py-2 rounded-lg font-medium ${
                  config.enabled
                    ? 'bg-red-100 text-red-700 hover:bg-red-200'
                    : 'bg-green-100 text-green-700 hover:bg-green-200'
                }`}
              >
                {config.enabled ? 'Disable Bot' : 'Enable Bot'}
              </button>
            </div>
          </div>

          {/* Configuration Form */}
          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center gap-3">
                <Settings className="h-6 w-6 text-blue-600" />
                <h2 className="text-lg font-semibold text-gray-900">Trading Configuration</h2>
              </div>
            </div>

            <div className="p-6 space-y-6">
              {/* Bot Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Bot Name
                </label>
                <input
                  type="text"
                  value={config.name}
                  onChange={(e) => setConfig({ ...config, name: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Strategy */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Strategy
                </label>
                <input
                  type="text"
                  value={config.strategy}
                  onChange={(e) => setConfig({ ...config, strategy: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Trading Symbols */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Trading Symbols
                </label>
                <div className="flex gap-2 mb-2">
                  <input
                    type="text"
                    value={symbolInput}
                    onChange={(e) => setSymbolInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleAddSymbol()}
                    placeholder="Add symbol (e.g., AAPL)"
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <button
                    onClick={handleAddSymbol}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    Add
                  </button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {config.symbols.map((symbol) => (
                    <span
                      key={symbol}
                      className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800"
                    >
                      {symbol}
                      <button
                        onClick={() => handleRemoveSymbol(symbol)}
                        className="ml-2 text-blue-600 hover:text-blue-800"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              </div>

              {/* Paper Trading */}
              <div className="flex items-start">
                <div className="flex items-center h-5">
                  <input
                    type="checkbox"
                    checked={config.paperTrading}
                    onChange={(e) => setConfig({ ...config, paperTrading: e.target.checked })}
                    className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                </div>
                <div className="ml-3">
                  <label className="font-medium text-gray-900">Paper Trading Mode</label>
                  <p className="text-sm text-gray-500">
                    Trade with simulated money instead of real capital
                  </p>
                </div>
              </div>

              {/* Simulated Capital (only if paper trading) */}
              {config.paperTrading && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Simulated Capital ($)
                  </label>
                  <input
                    type="number"
                    value={config.simulatedCapital || 0}
                    onChange={(e) => setConfig({ ...config, simulatedCapital: parseFloat(e.target.value) })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              )}

              {/* Risk Per Trade */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Risk Per Trade (%)
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={config.riskPerTrade}
                  onChange={(e) => setConfig({ ...config, riskPerTrade: parseFloat(e.target.value) })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="mt-1 text-sm text-gray-500">
                  Maximum percentage of capital to risk on a single trade
                </p>
              </div>

              {/* Max Position Size */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Max Position Size (%)
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={config.maxPositionSize}
                  onChange={(e) => setConfig({ ...config, maxPositionSize: parseFloat(e.target.value) })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="mt-1 text-sm text-gray-500">
                  Maximum percentage of portfolio for a single position
                </p>
              </div>

              {/* Max Portfolio Heat */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Max Portfolio Heat (%)
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={config.maxPortfolioHeat}
                  onChange={(e) => setConfig({ ...config, maxPortfolioHeat: parseFloat(e.target.value) })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="mt-1 text-sm text-gray-500">
                  Maximum total risk across all open positions
                </p>
              </div>

              {/* Save Button */}
              <div className="pt-4 border-t border-gray-200">
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="inline-flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Save className="h-4 w-4 mr-2" />
                  {saving ? 'Saving...' : 'Save Configuration'}
                </button>
              </div>
            </div>
          </div>

          {/* Warning Box */}
          <div className="mt-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5" />
              <div>
                <h3 className="text-sm font-medium text-yellow-900 mb-1">Important Notes</h3>
                <ul className="text-sm text-yellow-800 space-y-1">
                  <li>• Changes to bot configuration require a bot restart to take effect</li>
                  <li>• Always test configuration changes in paper trading mode first</li>
                  <li>• Risk parameters help protect your capital from excessive losses</li>
                  <li>• Monitor bot performance regularly and adjust settings as needed</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}
