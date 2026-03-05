'use client';

import { useState, useEffect } from 'react';
import { AlertTriangle, Power, RefreshCw } from 'lucide-react';

interface EmergencyStopStatus {
  equity: boolean;
  crypto: boolean;
}

export default function EmergencyStopControl() {
  const [status, setStatus] = useState<EmergencyStopStatus>({ equity: false, crypto: false });
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const fetchStatus = async () => {
    try {
      const response = await fetch('/api/bot/emergency-stop');
      if (response.ok) {
        const data = await response.json();
        setStatus(data);
      }
    } catch (error) {
      console.error('Failed to fetch emergency stop status:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const triggerEmergencyStop = async (botName: string) => {
    if (!confirm(`⚠️ EMERGENCY STOP\n\nThis will immediately:\n- Stop all trading\n- Close all open positions at market price\n- Halt the ${botName} bot\n\nAre you sure?`)) {
      return;
    }

    setActionLoading(botName);
    try {
      const response = await fetch('/api/bot/emergency-stop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ botName }),
      });

      if (response.ok) {
        await fetchStatus();
        alert(`✅ Emergency stop triggered for ${botName}`);
      } else {
        const error = await response.json();
        alert(`❌ Failed to trigger emergency stop: ${error.error}`);
      }
    } catch (error) {
      console.error('Emergency stop error:', error);
      alert('❌ Failed to trigger emergency stop');
    } finally {
      setActionLoading(null);
    }
  };

  const releaseEmergencyStop = async (botName: string) => {
    if (!confirm(`Release emergency stop for ${botName}?\n\nThis will allow the bot to resume trading.`)) {
      return;
    }

    setActionLoading(botName);
    try {
      const response = await fetch('/api/bot/emergency-stop', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ botName }),
      });

      if (response.ok) {
        await fetchStatus();
        alert(`✅ Emergency stop released for ${botName}`);
      } else {
        const error = await response.json();
        alert(`❌ Failed to release emergency stop: ${error.error}`);
      }
    } catch (error) {
      console.error('Release emergency stop error:', error);
      alert('❌ Failed to release emergency stop');
    } finally {
      setActionLoading(null);
    }
  };

  if (loading) {
    return (
      <div className="rounded-lg border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-6">
        <div className="flex items-center gap-2 mb-4">
          <AlertTriangle className="h-5 w-5 text-red-500" />
          <h3 className="text-lg font-semibold">Emergency Stop Controls</h3>
        </div>
        <div className="text-sm text-gray-500">Loading...</div>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-red-500" />
          <h3 className="text-lg font-semibold">Emergency Stop Controls</h3>
        </div>
        <button
          onClick={fetchStatus}
          className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
          title="Refresh status"
        >
          <RefreshCw className="h-4 w-4" />
        </button>
      </div>

      <div className="space-y-4">
        {/* Equity Bot */}
        <div className="flex items-center justify-between p-4 rounded-lg bg-gray-50 dark:bg-gray-800">
          <div className="flex items-center gap-3">
            <div className={`w-3 h-3 rounded-full ${status.equity ? 'bg-red-500 animate-pulse' : 'bg-green-500'}`} />
            <div>
              <div className="font-medium">Equity Bot</div>
              <div className="text-sm text-gray-500">
                {status.equity ? '🛑 Emergency Stop Active' : '✅ Trading Normally'}
              </div>
            </div>
          </div>
          <div className="flex gap-2">
            {status.equity ? (
              <button
                onClick={() => releaseEmergencyStop('quantshift-equity')}
                disabled={actionLoading === 'quantshift-equity'}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {actionLoading === 'quantshift-equity' ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    Releasing...
                  </>
                ) : (
                  <>
                    <Power className="h-4 w-4" />
                    Release Stop
                  </>
                )}
              </button>
            ) : (
              <button
                onClick={() => triggerEmergencyStop('quantshift-equity')}
                disabled={actionLoading === 'quantshift-equity'}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {actionLoading === 'quantshift-equity' ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    Stopping...
                  </>
                ) : (
                  <>
                    <AlertTriangle className="h-4 w-4" />
                    Emergency Stop
                  </>
                )}
              </button>
            )}
          </div>
        </div>

        {/* Crypto Bot */}
        <div className="flex items-center justify-between p-4 rounded-lg bg-gray-50 dark:bg-gray-800">
          <div className="flex items-center gap-3">
            <div className={`w-3 h-3 rounded-full ${status.crypto ? 'bg-red-500 animate-pulse' : 'bg-green-500'}`} />
            <div>
              <div className="font-medium">Crypto Bot</div>
              <div className="text-sm text-gray-500">
                {status.crypto ? '🛑 Emergency Stop Active' : '✅ Trading Normally'}
              </div>
            </div>
          </div>
          <div className="flex gap-2">
            {status.crypto ? (
              <button
                onClick={() => releaseEmergencyStop('quantshift-crypto')}
                disabled={actionLoading === 'quantshift-crypto'}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {actionLoading === 'quantshift-crypto' ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    Releasing...
                  </>
                ) : (
                  <>
                    <Power className="h-4 w-4" />
                    Release Stop
                  </>
                )}
              </button>
            ) : (
              <button
                onClick={() => triggerEmergencyStop('quantshift-crypto')}
                disabled={actionLoading === 'quantshift-crypto'}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {actionLoading === 'quantshift-crypto' ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    Stopping...
                  </>
                ) : (
                  <>
                    <AlertTriangle className="h-4 w-4" />
                    Emergency Stop
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="mt-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
        <div className="flex gap-2">
          <AlertTriangle className="h-5 w-5 text-yellow-600 dark:text-yellow-500 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-yellow-800 dark:text-yellow-200">
            <strong>Warning:</strong> Emergency stop will immediately close all positions at market price and halt trading. Use only in emergencies.
          </div>
        </div>
      </div>
    </div>
  );
}
