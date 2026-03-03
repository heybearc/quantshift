'use client';

import { useState } from 'react';
import { AlertTriangle } from 'lucide-react';

interface EmergencyStopButtonProps {
  botName: 'quantshift-equity' | 'quantshift-crypto';
  botDisplayName?: string;
}

export function EmergencyStopButton({ botName, botDisplayName }: EmergencyStopButtonProps) {
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const displayName = botDisplayName || (botName === 'quantshift-equity' ? 'Equity Bot' : 'Crypto Bot');

  const handleEmergencyStop = async () => {
    setIsLoading(true);
    setMessage(null);

    try {
      const response = await fetch('/api/bot/emergency-stop', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ botName }),
      });

      const data = await response.json();

      if (response.ok) {
        setMessage({
          type: 'success',
          text: `Emergency stop triggered for ${displayName}. All positions will be closed immediately.`,
        });
        setIsConfirmOpen(false);
      } else {
        setMessage({
          type: 'error',
          text: data.error || 'Failed to trigger emergency stop',
        });
      }
    } catch (error) {
      setMessage({
        type: 'error',
        text: 'Network error. Please try again or use Redis command directly.',
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-2">
      <button
        onClick={() => setIsConfirmOpen(true)}
        disabled={isLoading}
        className="inline-flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-medium rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <AlertTriangle className="w-4 h-4" />
        Emergency Stop {displayName}
      </button>

      {message && (
        <div
          className={`p-3 rounded-md text-sm ${
            message.type === 'success'
              ? 'bg-green-50 text-green-800 border border-green-200'
              : 'bg-red-50 text-red-800 border border-red-200'
          }`}
        >
          {message.text}
        </div>
      )}

      {isConfirmOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 shadow-xl">
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0">
                <AlertTriangle className="w-6 h-6 text-red-600" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Emergency Stop Confirmation
                </h3>
                <p className="text-sm text-gray-600 mb-4">
                  This will immediately:
                </p>
                <ul className="text-sm text-gray-600 mb-4 space-y-1 list-disc list-inside">
                  <li>Close all open positions at market price</li>
                  <li>Stop the {displayName} trading loop</li>
                  <li>Update bot status to EMERGENCY_STOPPED</li>
                </ul>
                <p className="text-sm font-semibold text-red-600 mb-6">
                  This action cannot be undone. Are you sure?
                </p>
                <div className="flex gap-3">
                  <button
                    onClick={() => setIsConfirmOpen(false)}
                    disabled={isLoading}
                    className="flex-1 px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-800 font-medium rounded-md transition-colors disabled:opacity-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleEmergencyStop}
                    disabled={isLoading}
                    className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-medium rounded-md transition-colors disabled:opacity-50"
                  >
                    {isLoading ? 'Stopping...' : 'Yes, Emergency Stop'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
