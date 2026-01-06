'use client';

import { ProtectedRoute } from '@/components/protected-route';
import { LayoutWrapper } from '@/components/layout-wrapper';
import { useAuth } from '@/lib/auth-context';
import { useState, useEffect } from 'react';
import { Shield, Trash2, RefreshCw, Clock, Monitor, MapPin } from 'lucide-react';

interface UserSession {
  id: string;
  userId: string;
  user: {
    email: string;
    full_name: string | null;
    role: string;
  };
  isActive: boolean;
  lastActivityAt: string;
  ipAddress: string | null;
  userAgent: string | null;
  createdAt: string;
}

export default function SessionsPage() {
  const { user, loading: authLoading } = useAuth();
  const [sessions, setSessions] = useState<UserSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [terminating, setTerminating] = useState<string | null>(null);

  useEffect(() => {
    // Wait for auth to finish loading before checking role
    if (authLoading) {
      return;
    }

    if (user?.role !== 'ADMIN') {
      window.location.href = '/dashboard';
      return;
    }
    loadSessions();
  }, [user, authLoading]);

  const loadSessions = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/admin/sessions', {
        credentials: 'include'
      });
      const data = await response.json();
      if (data.success) {
        setSessions(data.data);
      }
    } catch (error) {
      console.error('Error loading sessions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTerminate = async (sessionId: string) => {
    if (!confirm('Are you sure you want to terminate this session?')) return;

    try {
      setTerminating(sessionId);
      const response = await fetch(`/api/admin/sessions/${sessionId}`, {
        method: 'DELETE',
        credentials: 'include'
      });

      const data = await response.json();

      if (data.success) {
        loadSessions();
      } else {
        alert('Failed to terminate session');
      }
    } catch (error) {
      console.error('Error terminating session:', error);
      alert('Failed to terminate session');
    } finally {
      setTerminating(null);
    }
  };

  const getBrowserInfo = (userAgent: string | null) => {
    if (!userAgent) return 'Unknown';
    
    if (userAgent.includes('Chrome')) return 'Chrome';
    if (userAgent.includes('Firefox')) return 'Firefox';
    if (userAgent.includes('Safari')) return 'Safari';
    if (userAgent.includes('Edge')) return 'Edge';
    return 'Other';
  };

  const getTimeSince = (date: string) => {
    const seconds = Math.floor((new Date().getTime() - new Date(date).getTime()) / 1000);
    
    if (seconds < 60) return `${seconds}s ago`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
  };

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
              <p className="text-gray-600">Loading sessions...</p>
            </div>
          </div>
        </LayoutWrapper>
      </ProtectedRoute>
    );
  }

  const activeSessions = sessions.filter(s => s.isActive);
  const inactiveSessions = sessions.filter(s => !s.isActive);

  return (
    <ProtectedRoute>
      <LayoutWrapper>
        <div className="min-h-screen bg-gray-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* Header */}
            <div className="flex justify-between items-center mb-8">
              <div>
                <div className="flex items-center gap-3 mb-2">
                  <Shield className="h-8 w-8 text-blue-600" />
                  <h1 className="text-3xl font-bold text-gray-900">Session Management</h1>
                </div>
                <p className="text-gray-600">Monitor and manage active user sessions</p>
              </div>
              <button
                onClick={loadSessions}
                className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </button>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-center">
                  <div className="p-3 bg-green-50 rounded-lg">
                    <Shield className="h-6 w-6 text-green-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-2xl font-bold text-gray-900">{activeSessions.length}</p>
                    <p className="text-sm text-gray-600">Active Sessions</p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-center">
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <Clock className="h-6 w-6 text-gray-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-2xl font-bold text-gray-900">{inactiveSessions.length}</p>
                    <p className="text-sm text-gray-600">Inactive Sessions</p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-center">
                  <div className="p-3 bg-blue-50 rounded-lg">
                    <Monitor className="h-6 w-6 text-blue-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-2xl font-bold text-gray-900">{sessions.length}</p>
                    <p className="text-sm text-gray-600">Total Sessions</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Active Sessions */}
            <div className="mb-8">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Active Sessions</h2>
              {activeSessions.length === 0 ? (
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
                  <Shield className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No Active Sessions</h3>
                  <p className="text-gray-600">There are currently no active user sessions.</p>
                </div>
              ) : (
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            User
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Last Activity
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Browser
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            IP Address
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Started
                          </th>
                          <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Actions
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {activeSessions.map((session) => (
                          <tr key={session.id} className="hover:bg-gray-50">
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div>
                                <div className="text-sm font-medium text-gray-900">
                                  {session.user.full_name || session.user.email}
                                </div>
                                <div className="text-sm text-gray-500">{session.user.email}</div>
                                <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                                  session.user.role === 'ADMIN' 
                                    ? 'bg-purple-100 text-purple-800' 
                                    : 'bg-gray-100 text-gray-800'
                                }`}>
                                  {session.user.role}
                                </span>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center text-sm text-gray-900">
                                <Clock className="h-4 w-4 mr-1 text-gray-400" />
                                {getTimeSince(session.lastActivityAt)}
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center text-sm text-gray-900">
                                <Monitor className="h-4 w-4 mr-1 text-gray-400" />
                                {getBrowserInfo(session.userAgent)}
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center text-sm text-gray-900">
                                <MapPin className="h-4 w-4 mr-1 text-gray-400" />
                                {session.ipAddress || 'Unknown'}
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {new Date(session.createdAt).toLocaleString()}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                              <button
                                onClick={() => handleTerminate(session.id)}
                                disabled={terminating === session.id}
                                className="text-red-600 hover:text-red-900 disabled:opacity-50"
                              >
                                <Trash2 className="h-4 w-4" />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>

            {/* Inactive Sessions */}
            {inactiveSessions.length > 0 && (
              <div>
                <h2 className="text-xl font-bold text-gray-900 mb-4">Recent Inactive Sessions</h2>
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            User
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Last Activity
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Duration
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {inactiveSessions.slice(0, 10).map((session) => (
                          <tr key={session.id} className="opacity-60">
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm font-medium text-gray-900">
                                {session.user.full_name || session.user.email}
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {getTimeSince(session.lastActivityAt)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {new Date(session.createdAt).toLocaleString()}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </LayoutWrapper>
    </ProtectedRoute>
  );
}
