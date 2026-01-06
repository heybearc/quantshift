'use client';

import { ProtectedRoute } from '@/components/protected-route';
import { LayoutWrapper } from '@/components/layout-wrapper';
import { useAuth } from '@/lib/auth-context';
import { useState, useEffect } from 'react';
import { FileText, Search, Filter, Download } from 'lucide-react';

interface AuditLog {
  id: string;
  userId: string;
  user: {
    email: string;
    full_name: string | null;
  };
  action: string;
  resourceType: string;
  resourceId: string | null;
  changes: any;
  ipAddress: string | null;
  createdAt: string;
}

export default function AuditLogsPage() {
  const { user, loading: authLoading } = useAuth();
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterAction, setFilterAction] = useState('all');
  const [filterResource, setFilterResource] = useState('all');

  useEffect(() => {
    // Wait for auth to finish loading before checking role
    if (authLoading) {
      return;
    }

    if (user?.role !== 'ADMIN') {
      window.location.href = '/dashboard';
      return;
    }
    loadLogs();
  }, [user, authLoading]);

  const loadLogs = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/admin/audit-logs', {
        credentials: 'include'
      });
      const data = await response.json();
      if (data.success) {
        setLogs(data.data);
      }
    } catch (error) {
      console.error('Error loading audit logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const getActionColor = (action: string) => {
    if (action.includes('CREATE')) return 'bg-green-100 text-green-800';
    if (action.includes('UPDATE')) return 'bg-blue-100 text-blue-800';
    if (action.includes('DELETE')) return 'bg-red-100 text-red-800';
    if (action.includes('LOGIN')) return 'bg-purple-100 text-purple-800';
    return 'bg-slate-800 text-slate-100';
  };

  const getActionIcon = (action: string) => {
    if (action.includes('CREATE')) return '✨';
    if (action.includes('UPDATE')) return '✏️';
    if (action.includes('DELETE')) return '🗑️';
    if (action.includes('LOGIN')) return '🔐';
    return '📝';
  };

  const filteredLogs = logs.filter(log => {
    const matchesSearch = 
      log.user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.action.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.resourceType.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesAction = filterAction === 'all' || log.action.includes(filterAction.toUpperCase());
    const matchesResource = filterResource === 'all' || log.resourceType === filterResource;

    return matchesSearch && matchesAction && matchesResource;
  });

  const uniqueActions = Array.from(new Set(logs.map(l => l.action.split('_')[0])));
  const uniqueResources = Array.from(new Set(logs.map(l => l.resourceType)));

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
              <p className="text-slate-400">Loading audit logs...</p>
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
                  <FileText className="h-8 w-8 text-blue-600" />
                  <h1 className="text-3xl font-bold text-white">Audit Logs</h1>
                </div>
                <p className="text-slate-400">View system activity and user actions</p>
              </div>
              <button
                onClick={() => alert('Export functionality coming soon')}
                className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                <Download className="h-4 w-4 mr-2" />
                Export
              </button>
            </div>

            {/* Filters */}
            <div className="bg-slate-800/50 rounded-lg shadow-sm border border-slate-700 p-4 mb-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Search */}
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-slate-500" />
                  <input
                    type="text"
                    placeholder="Search logs..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                {/* Action Filter */}
                <div className="relative">
                  <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-slate-500" />
                  <select
                    value={filterAction}
                    onChange={(e) => setFilterAction(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 appearance-none"
                  >
                    <option value="all">All Actions</option>
                    {uniqueActions.map(action => (
                      <option key={action} value={action}>{action}</option>
                    ))}
                  </select>
                </div>

                {/* Resource Filter */}
                <div className="relative">
                  <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-slate-500" />
                  <select
                    value={filterResource}
                    onChange={(e) => setFilterResource(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 appearance-none"
                  >
                    <option value="all">All Resources</option>
                    {uniqueResources.map(resource => (
                      <option key={resource} value={resource}>{resource}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-slate-800/50 rounded-lg shadow-sm border border-slate-700 p-4">
                <p className="text-2xl font-bold text-white">{logs.length}</p>
                <p className="text-sm text-slate-400">Total Logs</p>
              </div>
              <div className="bg-slate-800/50 rounded-lg shadow-sm border border-slate-700 p-4">
                <p className="text-2xl font-bold text-white">{filteredLogs.length}</p>
                <p className="text-sm text-slate-400">Filtered Results</p>
              </div>
              <div className="bg-slate-800/50 rounded-lg shadow-sm border border-slate-700 p-4">
                <p className="text-2xl font-bold text-white">{uniqueActions.length}</p>
                <p className="text-sm text-slate-400">Action Types</p>
              </div>
              <div className="bg-slate-800/50 rounded-lg shadow-sm border border-slate-700 p-4">
                <p className="text-2xl font-bold text-white">{uniqueResources.length}</p>
                <p className="text-sm text-slate-400">Resource Types</p>
              </div>
            </div>

            {/* Logs Table */}
            {filteredLogs.length === 0 ? (
              <div className="bg-slate-800/50 rounded-lg shadow-sm border border-slate-700 p-12 text-center">
                <FileText className="h-12 w-12 text-slate-500 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-white mb-2">No Audit Logs Found</h3>
                <p className="text-slate-400">
                  {searchTerm || filterAction !== 'all' || filterResource !== 'all'
                    ? 'Try adjusting your filters'
                    : 'Audit logs will appear here as users perform actions'}
                </p>
              </div>
            ) : (
              <div className="bg-slate-800/50 rounded-lg shadow-sm border border-slate-700 overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-slate-900">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                          Timestamp
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                          User
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                          Action
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                          Resource
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                          IP Address
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-slate-800/50 divide-y divide-gray-200">
                      {filteredLogs.map((log) => (
                        <tr key={log.id} className="hover:bg-slate-900">
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-400">
                            {new Date(log.createdAt).toLocaleString()}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm font-medium text-white">
                              {log.user.full_name || log.user.email}
                            </div>
                            <div className="text-sm text-slate-400">{log.user.email}</div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getActionColor(log.action)}`}>
                              <span className="mr-1">{getActionIcon(log.action)}</span>
                              {log.action}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-white">{log.resourceType}</div>
                            {log.resourceId && (
                              <div className="text-xs text-slate-400">{log.resourceId.substring(0, 8)}...</div>
                            )}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-400">
                            {log.ipAddress || 'Unknown'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </div>
      </LayoutWrapper>
    </ProtectedRoute>
  );
}
