'use client';

import { ProtectedRoute } from '@/components/protected-route';
import { LayoutWrapper } from '@/components/layout-wrapper';
import { useAuth } from '@/lib/auth-context';
import { useState, useEffect } from 'react';
import { Mail, Settings as SettingsIcon, Save, Send, CheckCircle, AlertCircle } from 'lucide-react';

interface EmailConfig {
  authType: 'gmail' | 'smtp';
  gmailEmail: string;
  gmailAppPassword: string;
  smtpServer: string;
  smtpPort: string;
  smtpUser: string;
  smtpPassword: string;
  smtpSecure: boolean;
  fromEmail: string;
  fromName: string;
  replyToEmail: string;
}

type TabType = 'email' | 'general' | 'notifications';

export default function AdminSettingsPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<TabType>('email');
  const [emailConfig, setEmailConfig] = useState<EmailConfig>({
    authType: 'gmail',
    gmailEmail: '',
    gmailAppPassword: '',
    smtpServer: 'smtp.gmail.com',
    smtpPort: '587',
    smtpUser: '',
    smtpPassword: '',
    smtpSecure: true,
    fromEmail: '',
    fromName: 'QuantShift Trading Platform',
    replyToEmail: '',
  });

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [statusMessage, setStatusMessage] = useState('');

  useEffect(() => {
    if (user?.role !== 'ADMIN') {
      window.location.href = '/dashboard';
      return;
    }
    loadConfiguration();
  }, [user]);

  const loadConfiguration = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/admin/settings/email');
      const data = await response.json();

      if (data.success && data.data) {
        setEmailConfig(data.data);
      }
    } catch (error) {
      console.error('Error loading email configuration:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setStatus('idle');
    setStatusMessage('');

    try {
      const response = await fetch('/api/admin/settings/email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(emailConfig),
      });

      const data = await response.json();

      if (data.success) {
        setStatus('success');
        setStatusMessage('Email configuration saved successfully!');
        setTimeout(() => {
          setStatus('idle');
          setStatusMessage('');
        }, 3000);
      } else {
        throw new Error(data.error || 'Failed to save configuration');
      }
    } catch (error) {
      console.error('Error saving configuration:', error);
      setStatus('error');
      setStatusMessage('Failed to save configuration. Please try again.');
      setTimeout(() => {
        setStatus('idle');
        setStatusMessage('');
      }, 3000);
    } finally {
      setSaving(false);
    }
  };

  const handleTestEmail = async () => {
    setTesting(true);
    setStatus('idle');
    setStatusMessage('');

    try {
      const response = await fetch('/api/admin/settings/email/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(emailConfig),
      });

      const data = await response.json();

      if (data.success) {
        setStatus('success');
        setStatusMessage('✅ Test email sent successfully! Check your inbox.');
      } else {
        throw new Error(data.error || 'Failed to send test email');
      }
    } catch (error) {
      console.error('Error sending test email:', error);
      setStatus('error');
      setStatusMessage('❌ Failed to send test email. Please check your configuration.');
    } finally {
      setTesting(false);
      setTimeout(() => {
        setStatus('idle');
        setStatusMessage('');
      }, 5000);
    }
  };

  const isGmailConfigValid = emailConfig.authType === 'gmail' && emailConfig.gmailEmail && emailConfig.gmailAppPassword;
  const isSmtpConfigValid = emailConfig.authType === 'smtp' && emailConfig.smtpServer && emailConfig.smtpUser && emailConfig.smtpPassword;
  const isConfigValid = (isGmailConfigValid || isSmtpConfigValid) && emailConfig.fromEmail && emailConfig.fromName;

  if (user?.role !== 'ADMIN') {
    return null;
  }

  if (loading) {
    return (
      <ProtectedRoute>
        <LayoutWrapper>
          <div className="min-h-screen flex items-center justify-center">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Loading settings...</p>
            </div>
          </div>
        </LayoutWrapper>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute>
      <LayoutWrapper>
        <div className="min-h-screen bg-gray-50">
          <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* Header */}
            <div className="mb-8">
              <div className="flex items-center gap-3 mb-2">
                <SettingsIcon className="h-8 w-8 text-blue-600" />
                <h1 className="text-3xl font-bold text-gray-900">Platform Settings</h1>
              </div>
              <p className="text-gray-600">
                Configure email notifications, platform preferences, and system settings
              </p>
            </div>

            {/* Status Message */}
            {status !== 'idle' && statusMessage && (
              <div className={`mb-6 p-4 rounded-lg flex items-center gap-3 ${
                status === 'success' 
                  ? 'bg-green-50 border border-green-200' 
                  : 'bg-red-50 border border-red-200'
              }`}>
                {status === 'success' ? (
                  <CheckCircle className="h-5 w-5 text-green-600" />
                ) : (
                  <AlertCircle className="h-5 w-5 text-red-600" />
                )}
                <p className={`text-sm font-medium ${status === 'success' ? 'text-green-800' : 'text-red-800'}`}>
                  {statusMessage}
                </p>
              </div>
            )}

            {/* Tabs */}
            <div className="bg-white rounded-lg shadow-sm mb-6">
              <div className="border-b border-gray-200">
                <nav className="flex -mb-px">
                  <button
                    onClick={() => setActiveTab('email')}
                    className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                      activeTab === 'email'
                        ? 'border-blue-600 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <Mail className="h-4 w-4" />
                      Email Configuration
                    </div>
                  </button>
                  <button
                    onClick={() => setActiveTab('general')}
                    className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                      activeTab === 'general'
                        ? 'border-blue-600 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <SettingsIcon className="h-4 w-4" />
                      General Settings
                    </div>
                  </button>
                </nav>
              </div>

              {/* Email Configuration Tab */}
              {activeTab === 'email' && (
                <div className="p-6 space-y-6">
                  {/* Email Provider Selection */}
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Email Provider</h3>
                    <div className="flex space-x-4">
                      <button
                        onClick={() => setEmailConfig({ ...emailConfig, authType: 'gmail' })}
                        className={`px-6 py-3 rounded-lg font-medium transition-colors ${
                          emailConfig.authType === 'gmail'
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                      >
                        📧 Gmail (Recommended)
                      </button>
                      <button
                        onClick={() => setEmailConfig({ ...emailConfig, authType: 'smtp' })}
                        className={`px-6 py-3 rounded-lg font-medium transition-colors ${
                          emailConfig.authType === 'smtp'
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                      >
                        🔧 Custom SMTP
                      </button>
                    </div>
                  </div>

                  {/* Gmail Configuration */}
                  {emailConfig.authType === 'gmail' && (
                    <div className="space-y-6">
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                        <div className="flex items-start">
                          <div className="flex-shrink-0">
                            <span className="text-2xl">💡</span>
                          </div>
                          <div className="ml-3">
                            <h4 className="text-sm font-medium text-blue-800">Gmail App Password Setup</h4>
                            <div className="mt-2 text-sm text-blue-700">
                              <p className="mb-2">To use Gmail, you need to generate an App Password:</p>
                              <ol className="list-decimal list-inside space-y-1">
                                <li>Go to your Google Account settings</li>
                                <li>Enable 2-Step Verification if not already enabled</li>
                                <li>Go to Security → App passwords</li>
                                <li>Generate a new app password for "Mail"</li>
                                <li>Use that 16-character password below</li>
                              </ol>
                              <p className="mt-3 font-semibold text-red-700">⚠️ IMPORTANT: Remove ALL spaces from the app password!</p>
                              <p className="text-xs">Gmail shows: "abcd efgh ijkl mnop" → Enter: "abcdefghijklmnop"</p>
                            </div>
                          </div>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Gmail Email Address *
                          </label>
                          <input
                            type="email"
                            placeholder="your-email@gmail.com"
                            value={emailConfig.gmailEmail}
                            onChange={(e) => setEmailConfig({ ...emailConfig, gmailEmail: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Gmail App Password *
                          </label>
                          <input
                            type="password"
                            placeholder="16-character app password (no spaces)"
                            value={emailConfig.gmailAppPassword}
                            onChange={(e) => setEmailConfig({ ...emailConfig, gmailAppPassword: e.target.value.replace(/\s/g, '') })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />
                          <p className="text-xs text-red-600 mt-1 font-medium">⚠️ Spaces will be automatically removed</p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* SMTP Configuration */}
                  {emailConfig.authType === 'smtp' && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">SMTP Server *</label>
                        <input
                          type="text"
                          placeholder="smtp.example.com"
                          value={emailConfig.smtpServer}
                          onChange={(e) => setEmailConfig({ ...emailConfig, smtpServer: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">SMTP Port *</label>
                        <select
                          value={emailConfig.smtpPort}
                          onChange={(e) => setEmailConfig({ ...emailConfig, smtpPort: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                          <option value="587">587 (STARTTLS)</option>
                          <option value="465">465 (SSL)</option>
                          <option value="25">25 (Plain)</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Username *</label>
                        <input
                          type="text"
                          placeholder="username or email"
                          value={emailConfig.smtpUser}
                          onChange={(e) => setEmailConfig({ ...emailConfig, smtpUser: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Password *</label>
                        <input
                          type="password"
                          placeholder="SMTP password"
                          value={emailConfig.smtpPassword}
                          onChange={(e) => setEmailConfig({ ...emailConfig, smtpPassword: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      <div className="md:col-span-2">
                        <label className="flex items-center">
                          <input
                            type="checkbox"
                            checked={emailConfig.smtpSecure}
                            onChange={(e) => setEmailConfig({ ...emailConfig, smtpSecure: e.target.checked })}
                            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                          />
                          <span className="ml-2 text-sm text-gray-700">Use secure connection (TLS/SSL)</span>
                        </label>
                      </div>
                    </div>
                  )}

                  {/* Common Email Settings */}
                  <div className="pt-6 border-t border-gray-200">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Email Settings</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">From Email *</label>
                        <input
                          type="email"
                          placeholder="noreply@quantshift.local"
                          value={emailConfig.fromEmail}
                          onChange={(e) => setEmailConfig({ ...emailConfig, fromEmail: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        <p className="text-xs text-gray-500 mt-1">Email address that appears in "From" field</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">From Name *</label>
                        <input
                          type="text"
                          placeholder="QuantShift Trading Platform"
                          value={emailConfig.fromName}
                          onChange={(e) => setEmailConfig({ ...emailConfig, fromName: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        <p className="text-xs text-gray-500 mt-1">Display name for outgoing emails</p>
                      </div>
                      <div className="md:col-span-2">
                        <label className="block text-sm font-medium text-gray-700 mb-2">Reply-To Email</label>
                        <input
                          type="email"
                          placeholder="admin@quantshift.local (optional)"
                          value={emailConfig.replyToEmail}
                          onChange={(e) => setEmailConfig({ ...emailConfig, replyToEmail: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        <p className="text-xs text-gray-500 mt-1">Where replies should be sent (optional)</p>
                      </div>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="pt-6 border-t border-gray-200 flex flex-col sm:flex-row gap-4">
                    <button
                      onClick={handleSave}
                      disabled={!isConfigValid || saving}
                      className={`inline-flex items-center justify-center px-6 py-3 rounded-lg font-medium transition-colors ${
                        !isConfigValid
                          ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                          : saving
                          ? 'bg-blue-400 text-white cursor-not-allowed'
                          : 'bg-blue-600 hover:bg-blue-700 text-white'
                      }`}
                    >
                      <Save className="h-4 w-4 mr-2" />
                      {saving ? 'Saving...' : 'Save Configuration'}
                    </button>

                    <button
                      onClick={handleTestEmail}
                      disabled={!isConfigValid || testing}
                      className={`inline-flex items-center justify-center px-6 py-3 rounded-lg font-medium transition-colors ${
                        !isConfigValid
                          ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                          : testing
                          ? 'bg-green-400 text-white cursor-not-allowed'
                          : 'bg-green-600 hover:bg-green-700 text-white'
                      }`}
                    >
                      <Send className="h-4 w-4 mr-2" />
                      {testing ? 'Sending...' : 'Send Test Email'}
                    </button>
                  </div>

                  {/* Validation Warning */}
                  {!isConfigValid && (
                    <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                      <div className="flex items-start">
                        <AlertCircle className="h-5 w-5 text-yellow-600 mr-2 mt-0.5" />
                        <div className="text-sm text-yellow-700">
                          <p className="font-medium">Configuration incomplete</p>
                          <p>Please fill in all required fields to enable email functionality.</p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* General Settings Tab */}
              {activeTab === 'general' && (
                <div className="p-6">
                  <div className="text-center py-12">
                    <SettingsIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">General Settings</h3>
                    <p className="text-gray-600">Coming soon - Platform preferences and configuration</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </LayoutWrapper>
    </ProtectedRoute>
  );
}
