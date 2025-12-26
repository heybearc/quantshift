'use client';

import { ProtectedRoute } from '@/components/protected-route';
import { useState, useEffect } from 'react';
import { Mail, Save, TestTube, AlertCircle, CheckCircle } from 'lucide-react';
import Link from 'next/link';

interface EmailConfig {
  email: string;
  tradeAlerts: boolean;
  dailySummary: boolean;
  weeklyReport: boolean;
  errorAlerts: boolean;
}

export default function EmailPage() {
  const [config, setConfig] = useState<EmailConfig>({
    email: '',
    tradeAlerts: true,
    dailySummary: true,
    weeklyReport: false,
    errorAlerts: true,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    fetchEmailConfig();
  }, []);

  const fetchEmailConfig = async () => {
    try {
      const response = await fetch('/api/email/config');
      if (response.ok) {
        const data = await response.json();
        setConfig(data);
      }
    } catch (error) {
      console.error('Error fetching email config:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setMessage(null);
    try {
      const response = await fetch('/api/email/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });

      if (response.ok) {
        setMessage({ type: 'success', text: 'Email configuration saved successfully!' });
      } else {
        throw new Error('Failed to save configuration');
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to save email configuration. Please try again.' });
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    setTesting(true);
    setMessage(null);
    try {
      const response = await fetch('/api/email/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: config.email }),
      });

      if (response.ok) {
        setMessage({ type: 'success', text: 'Test email sent successfully! Check your inbox.' });
      } else {
        throw new Error('Failed to send test email');
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to send test email. Please check your email address.' });
    } finally {
      setTesting(false);
    }
  };

  if (loading) {
    return (
      <ProtectedRoute>
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
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
                <h1 className="text-3xl font-bold text-gray-900">Email Notifications</h1>
                <p className="mt-1 text-gray-600">
                  Configure email alerts for trading activity and bot status
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

          {/* Email Configuration Form */}
          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center gap-3">
                <Mail className="h-6 w-6 text-blue-600" />
                <h2 className="text-lg font-semibold text-gray-900">Email Settings</h2>
              </div>
            </div>

            <div className="p-6 space-y-6">
              {/* Email Address */}
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                  Email Address
                </label>
                <input
                  type="email"
                  id="email"
                  value={config.email}
                  onChange={(e) => setConfig({ ...config, email: e.target.value })}
                  placeholder="your.email@example.com"
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="mt-1 text-sm text-gray-500">
                  All trading notifications will be sent to this email address
                </p>
              </div>

              {/* Notification Types */}
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-4">Notification Types</h3>
                <div className="space-y-4">
                  {/* Trade Alerts */}
                  <div className="flex items-start">
                    <div className="flex items-center h-5">
                      <input
                        type="checkbox"
                        id="tradeAlerts"
                        checked={config.tradeAlerts}
                        onChange={(e) => setConfig({ ...config, tradeAlerts: e.target.checked })}
                        className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                      />
                    </div>
                    <div className="ml-3">
                      <label htmlFor="tradeAlerts" className="font-medium text-gray-900">
                        Trade Alerts
                      </label>
                      <p className="text-sm text-gray-500">
                        Get notified when the bot enters or exits a trade
                      </p>
                    </div>
                  </div>

                  {/* Daily Summary */}
                  <div className="flex items-start">
                    <div className="flex items-center h-5">
                      <input
                        type="checkbox"
                        id="dailySummary"
                        checked={config.dailySummary}
                        onChange={(e) => setConfig({ ...config, dailySummary: e.target.checked })}
                        className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                      />
                    </div>
                    <div className="ml-3">
                      <label htmlFor="dailySummary" className="font-medium text-gray-900">
                        Daily Summary
                      </label>
                      <p className="text-sm text-gray-500">
                        Receive a daily summary of trading activity and performance
                      </p>
                    </div>
                  </div>

                  {/* Weekly Report */}
                  <div className="flex items-start">
                    <div className="flex items-center h-5">
                      <input
                        type="checkbox"
                        id="weeklyReport"
                        checked={config.weeklyReport}
                        onChange={(e) => setConfig({ ...config, weeklyReport: e.target.checked })}
                        className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                      />
                    </div>
                    <div className="ml-3">
                      <label htmlFor="weeklyReport" className="font-medium text-gray-900">
                        Weekly Report
                      </label>
                      <p className="text-sm text-gray-500">
                        Get a comprehensive weekly performance report every Monday
                      </p>
                    </div>
                  </div>

                  {/* Error Alerts */}
                  <div className="flex items-start">
                    <div className="flex items-center h-5">
                      <input
                        type="checkbox"
                        id="errorAlerts"
                        checked={config.errorAlerts}
                        onChange={(e) => setConfig({ ...config, errorAlerts: e.target.checked })}
                        className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                      />
                    </div>
                    <div className="ml-3">
                      <label htmlFor="errorAlerts" className="font-medium text-gray-900">
                        Error Alerts
                      </label>
                      <p className="text-sm text-gray-500">
                        Immediate notification if the bot encounters an error or stops running
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-4 pt-4 border-t border-gray-200">
                <button
                  onClick={handleSave}
                  disabled={saving || !config.email}
                  className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Save className="h-4 w-4 mr-2" />
                  {saving ? 'Saving...' : 'Save Configuration'}
                </button>
                <button
                  onClick={handleTest}
                  disabled={testing || !config.email}
                  className="inline-flex items-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <TestTube className="h-4 w-4 mr-2" />
                  {testing ? 'Sending...' : 'Send Test Email'}
                </button>
              </div>
            </div>
          </div>

          {/* Info Box */}
          <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-blue-600 mt-0.5" />
              <div>
                <h3 className="text-sm font-medium text-blue-900 mb-1">Email Notification Tips</h3>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>• Trade alerts are sent immediately when positions are opened or closed</li>
                  <li>• Daily summaries are sent at 5:00 PM EST after market close</li>
                  <li>• Error alerts help you respond quickly to bot issues</li>
                  <li>• You can update these settings at any time</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}
