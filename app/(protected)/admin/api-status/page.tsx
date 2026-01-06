'use client';

import { ProtectedRoute } from '@/components/protected-route';
import { LayoutWrapper } from '@/components/layout-wrapper';
import { useAuth } from '@/lib/auth-context';
import { useState, useEffect } from 'react';
import { Zap, RefreshCw, CheckCircle, AlertCircle, XCircle, Clock } from 'lucide-react';

interface EndpointStatus {
  endpoint: string;
  method: string;
  status: 'operational' | 'degraded' | 'down';
  responseTime: number;
  lastChecked: string;
}

interface ApiStatusData {
  overall: {
    status: string;
    operational: number;
    degraded: number;
    down: number;
    total: number;
    avgResponseTime: number;
  };
  endpoints: EndpointStatus[];
  timestamp: string;
}

export default function ApiStatusPage() {
  const { user, loading: authLoading } = useAuth();
  const [apiStatus, setApiStatus] = useState<ApiStatusData | null>(null);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    if (authLoading) return;
    
    if (user?.role !== 'ADMIN') {
      window.location.href = '/dashboard';
      return;
    }
    
    loadApiStatus();
  }, [user, authLoading]);

  useEffect(() => {
    if (!autoRefresh) return;
    
    const interval = setInterval(() => {
      loadApiStatus();
    }, 60000); // Refresh every 60 seconds

    return () => clearInterval(interval);
  }, [autoRefresh]);

  const loadApiStatus = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/admin/api-status', {
        credentials: 'include'
      });
      const data = await response.json();
      if (data.success) {
        setApiStatus(data.data);
      }
    } catch (error) {
      console.error('Error loading API status:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'operational': return 'text-green-600 bg-green-50';
      case 'degraded': return 'text-yellow-600 bg-yellow-50';
      case 'down': return 'text-red-600 bg-red-50';
      default: return 'text-slate-400 bg-slate-900';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'operational': return <CheckCircle className="h-5 w-5" />;
      case 'degraded': return <AlertCircle className="h-5 w-5" />;
      case 'down': return <XCircle className="h-5 w-5" />;
      default: return <Clock className="h-5 w-5" />;
    }
  };

  const getResponseTimeColor = (ms: number) => {
    if (ms < 500) return 'text-green-600';
    if (ms < 1000) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (user?.role !== 'ADMIN') return null;

  if (loading && !apiStatus) {
    return (
      <ProtectedRoute>
        <LayoutWrapper>
          <div className="min-h-screen flex items-center justify-center">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-slate-400">Checking API status...</p>
            </div>
          </div>
        </LayoutWrapper>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute>
      <LayoutWrapper>
        <div className="min-h-screen bg-slate-900">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* Header */}
            <div className="flex justify-between items-center mb-8">
              <div>
                <div className="flex items-center gap-3 mb-2">
                  <Zap className="h-8 w-8 text-blue-600" />
                  <h1 className="text-3xl font-bold text-white">API Status Monitor</h1>
                </div>
                <p className="text-slate-400">Real-time API endpoint health and performance monitoring</p>
              </div>
              <div className="flex gap-3">
                <button
                  onClick={() => setAutoRefresh(!autoRefresh)}
                  className={`inline-flex items-center px-4 py-2 rounded-lg ${
                    autoRefresh 
                      ? 'bg-green-600 text-white hover:bg-green-700' 
                      : 'bg-slate-700 text-slate-200 hover:bg-gray-300'
                  }`}
                >
                  <Zap className="h-4 w-4 mr-2" />
                  {autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}
                </button>
                <button
                  onClick={loadApiStatus}
                  disabled={loading}
                  className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                  Refresh
                </button>
              </div>
            </div>

            {apiStatus && (
              <>
                {/* Overall Status Cards */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                  <div className="bg-slate-800/50 rounded-lg shadow-sm border border-slate-700 p-6">
                    <div className="flex items-center justify-between mb-2">
                      <CheckCircle className="h-8 w-8 text-green-600" />
                      <span className="text-3xl font-bold text-white">{apiStatus.overall.operational}</span>
                    </div>
                    <h3 className="text-sm font-medium text-slate-400">Operational</h3>
                  </div>

                  <div className="bg-slate-800/50 rounded-lg shadow-sm border border-slate-700 p-6">
                    <div className="flex items-center justify-between mb-2">
                      <AlertCircle className="h-8 w-8 text-yellow-600" />
                      <span className="text-3xl font-bold text-white">{apiStatus.overall.degraded}</span>
                    </div>
                    <h3 className="text-sm font-medium text-slate-400">Degraded</h3>
                  </div>

                  <div className="bg-slate-800/50 rounded-lg shadow-sm border border-slate-700 p-6">
                    <div className="flex items-center justify-between mb-2">
                      <XCircle className="h-8 w-8 text-red-600" />
                      <span className="text-3xl font-bold text-white">{apiStatus.overall.down}</span>
                    </div>
                    <h3 className="text-sm font-medium text-slate-400">Down</h3>
                  </div>

                  <div className="bg-slate-800/50 rounded-lg shadow-sm border border-slate-700 p-6">
                    <div className="flex items-center justify-between mb-2">
                      <Clock className="h-8 w-8 text-blue-600" />
                      <span className={`text-3xl font-bold ${getResponseTimeColor(apiStatus.overall.avgResponseTime)}`}>
                        {apiStatus.overall.avgResponseTime}ms
                      </span>
                    </div>
                    <h3 className="text-sm font-medium text-slate-400">Avg Response</h3>
                  </div>
                </div>

                {/* Endpoints Table */}
                <div className="bg-slate-800/50 rounded-lg shadow-sm border border-slate-700 overflow-hidden">
                  <div className="px-6 py-4 border-b border-slate-700">
                    <h2 className="text-lg font-semibold text-white">API Endpoints</h2>
                    <p className="text-sm text-slate-400 mt-1">
                      Last checked: {new Date(apiStatus.timestamp).toLocaleString()}
                    </p>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-slate-900">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                            Endpoint
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                            Method
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                            Status
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                            Response Time
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                            Last Checked
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-slate-800/50 divide-y divide-gray-200">
                        {apiStatus.endpoints.map((endpoint, index) => (
                          <tr key={index} className="hover:bg-slate-900">
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm font-mono text-white">{endpoint.endpoint}</div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className="inline-flex items-center px-2.5 py-0.5 rounded text-xs font-medium bg-slate-800 text-slate-100">
                                {endpoint.method}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-medium ${getStatusColor(endpoint.status)}`}>
                                {getStatusIcon(endpoint.status)}
                                {endpoint.status}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`text-sm font-medium ${getResponseTimeColor(endpoint.responseTime)}`}>
                                {endpoint.responseTime}ms
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-400">
                              {new Date(endpoint.lastChecked).toLocaleTimeString()}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Status Legend */}
                <div className="mt-6 bg-slate-800/50 rounded-lg shadow-sm border border-slate-700 p-6">
                  <h3 className="text-sm font-semibold text-white mb-3">Status Legend</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="flex items-center gap-2">
                      <CheckCircle className="h-5 w-5 text-green-600" />
                      <div>
                        <p className="text-sm font-medium text-white">Operational</p>
                        <p className="text-xs text-slate-400">Response time &lt; 2s, status 2xx/3xx</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <AlertCircle className="h-5 w-5 text-yellow-600" />
                      <div>
                        <p className="text-sm font-medium text-white">Degraded</p>
                        <p className="text-xs text-slate-400">Response time &gt; 2s or status 4xx</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <XCircle className="h-5 w-5 text-red-600" />
                      <div>
                        <p className="text-sm font-medium text-white">Down</p>
                        <p className="text-xs text-slate-400">Timeout or status 5xx</p>
                      </div>
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </LayoutWrapper>
    </ProtectedRoute>
  );
}
