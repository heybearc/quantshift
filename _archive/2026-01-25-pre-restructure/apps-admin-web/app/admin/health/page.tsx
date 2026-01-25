'use client';

import { ProtectedRoute } from '@/components/protected-route';
import { LayoutWrapper } from '@/components/layout-wrapper';
import { useAuth } from '@/lib/auth-context';
import { useState, useEffect } from 'react';
import { Activity, Server, Database, Cpu, HardDrive, Clock, RefreshCw, AlertCircle, CheckCircle } from 'lucide-react';

interface HealthData {
  status: 'healthy' | 'warning' | 'critical';
  timestamp: string;
  system: {
    platform: string;
    arch: string;
    nodeVersion: string;
    uptime: number;
    hostname: string;
  };
  memory: {
    total: number;
    used: number;
    free: number;
    usagePercent: number;
  };
  cpu: {
    cores: number;
    model: string;
    loadAverage: {
      '1min': number;
      '5min': number;
      '15min': number;
    };
  };
  database: {
    status: string;
    responseTime: number;
    connections: {
      users: number;
      activeSessions: number;
      auditLogs: number;
      releaseNotes: number;
    };
  };
}

export default function HealthMonitorPage() {
  const { user, loading: authLoading } = useAuth();
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    if (authLoading) return;
    
    if (user?.role !== 'ADMIN') {
      window.location.href = '/dashboard';
      return;
    }
    
    loadHealth();
  }, [user, authLoading]);

  useEffect(() => {
    if (!autoRefresh) return;
    
    const interval = setInterval(() => {
      loadHealth();
    }, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  }, [autoRefresh]);

  const loadHealth = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/admin/health', {
        credentials: 'include'
      });
      const data = await response.json();
      if (data.success) {
        setHealth(data.data);
      }
    } catch (error) {
      console.error('Error loading health metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatBytes = (bytes: number) => {
    const gb = bytes / (1024 ** 3);
    return `${gb.toFixed(2)} GB`;
  };

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${days}d ${hours}h ${minutes}m`;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-600 bg-green-50';
      case 'warning': return 'text-yellow-600 bg-yellow-50';
      case 'critical': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return <CheckCircle className="h-6 w-6" />;
      case 'warning': return <AlertCircle className="h-6 w-6" />;
      case 'critical': return <AlertCircle className="h-6 w-6" />;
      default: return <Activity className="h-6 w-6" />;
    }
  };

  if (user?.role !== 'ADMIN') return null;

  if (loading && !health) {
    return (
      <ProtectedRoute>
        <LayoutWrapper>
          <div className="min-h-screen flex items-center justify-center">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Loading health metrics...</p>
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
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* Header */}
            <div className="flex justify-between items-center mb-8">
              <div>
                <div className="flex items-center gap-3 mb-2">
                  <Activity className="h-8 w-8 text-blue-600" />
                  <h1 className="text-3xl font-bold text-gray-900">System Health Monitor</h1>
                </div>
                <p className="text-gray-600">Real-time system metrics and performance monitoring</p>
              </div>
              <div className="flex gap-3">
                <button
                  onClick={() => setAutoRefresh(!autoRefresh)}
                  className={`inline-flex items-center px-4 py-2 rounded-lg ${
                    autoRefresh 
                      ? 'bg-green-600 text-white hover:bg-green-700' 
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  <Activity className="h-4 w-4 mr-2" />
                  {autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}
                </button>
                <button
                  onClick={loadHealth}
                  className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Refresh
                </button>
              </div>
            </div>

            {health && (
              <>
                {/* Overall Status Card */}
                <div className={`rounded-lg shadow-sm border-2 p-6 mb-8 ${getStatusColor(health.status)}`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      {getStatusIcon(health.status)}
                      <div>
                        <h2 className="text-2xl font-bold capitalize">{health.status}</h2>
                        <p className="text-sm opacity-75">System Status</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm opacity-75">Last Updated</p>
                      <p className="font-medium">{new Date(health.timestamp).toLocaleTimeString()}</p>
                    </div>
                  </div>
                </div>

                {/* Metrics Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                  {/* Memory Usage */}
                  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <div className="flex items-center justify-between mb-4">
                      <HardDrive className="h-8 w-8 text-purple-600" />
                      <span className={`text-2xl font-bold ${
                        health.memory.usagePercent > 75 ? 'text-red-600' : 'text-gray-900'
                      }`}>
                        {health.memory.usagePercent.toFixed(1)}%
                      </span>
                    </div>
                    <h3 className="text-sm font-medium text-gray-600 mb-2">Memory Usage</h3>
                    <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                      <div 
                        className={`h-2 rounded-full ${
                          health.memory.usagePercent > 75 ? 'bg-red-600' : 'bg-purple-600'
                        }`}
                        style={{ width: `${health.memory.usagePercent}%` }}
                      ></div>
                    </div>
                    <p className="text-xs text-gray-500">
                      {formatBytes(health.memory.used)} / {formatBytes(health.memory.total)}
                    </p>
                  </div>

                  {/* CPU Load */}
                  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <div className="flex items-center justify-between mb-4">
                      <Cpu className="h-8 w-8 text-blue-600" />
                      <span className="text-2xl font-bold text-gray-900">
                        {health.cpu.loadAverage['1min'].toFixed(2)}
                      </span>
                    </div>
                    <h3 className="text-sm font-medium text-gray-600 mb-2">CPU Load (1min)</h3>
                    <p className="text-xs text-gray-500">
                      {health.cpu.cores} cores • {health.cpu.model.substring(0, 30)}...
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      5min: {health.cpu.loadAverage['5min'].toFixed(2)} • 
                      15min: {health.cpu.loadAverage['15min'].toFixed(2)}
                    </p>
                  </div>

                  {/* Database */}
                  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <div className="flex items-center justify-between mb-4">
                      <Database className="h-8 w-8 text-green-600" />
                      <span className={`text-2xl font-bold ${
                        health.database.status === 'healthy' ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {health.database.responseTime}ms
                      </span>
                    </div>
                    <h3 className="text-sm font-medium text-gray-600 mb-2">Database</h3>
                    <p className="text-xs text-gray-500 capitalize">
                      Status: {health.database.status}
                    </p>
                    <p className="text-xs text-gray-500">
                      {health.database.connections.users} users • 
                      {health.database.connections.activeSessions} sessions
                    </p>
                  </div>

                  {/* Uptime */}
                  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <div className="flex items-center justify-between mb-4">
                      <Clock className="h-8 w-8 text-orange-600" />
                      <Server className="h-8 w-8 text-gray-400" />
                    </div>
                    <h3 className="text-sm font-medium text-gray-600 mb-2">System Uptime</h3>
                    <p className="text-lg font-bold text-gray-900">
                      {formatUptime(health.system.uptime)}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {health.system.platform} • {health.system.arch}
                    </p>
                  </div>
                </div>

                {/* Detailed Information */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* System Information */}
                  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">System Information</h3>
                    <dl className="space-y-3">
                      <div className="flex justify-between">
                        <dt className="text-sm text-gray-600">Hostname</dt>
                        <dd className="text-sm font-medium text-gray-900">{health.system.hostname}</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-sm text-gray-600">Platform</dt>
                        <dd className="text-sm font-medium text-gray-900">{health.system.platform}</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-sm text-gray-600">Architecture</dt>
                        <dd className="text-sm font-medium text-gray-900">{health.system.arch}</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-sm text-gray-600">Node Version</dt>
                        <dd className="text-sm font-medium text-gray-900">{health.system.nodeVersion}</dd>
                      </div>
                    </dl>
                  </div>

                  {/* Database Statistics */}
                  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Database Statistics</h3>
                    <dl className="space-y-3">
                      <div className="flex justify-between">
                        <dt className="text-sm text-gray-600">Total Users</dt>
                        <dd className="text-sm font-medium text-gray-900">{health.database.connections.users}</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-sm text-gray-600">Active Sessions</dt>
                        <dd className="text-sm font-medium text-gray-900">{health.database.connections.activeSessions}</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-sm text-gray-600">Audit Logs</dt>
                        <dd className="text-sm font-medium text-gray-900">{health.database.connections.auditLogs}</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-sm text-gray-600">Release Notes</dt>
                        <dd className="text-sm font-medium text-gray-900">{health.database.connections.releaseNotes}</dd>
                      </div>
                    </dl>
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
