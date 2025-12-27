'use client';

import { ProtectedRoute } from '@/components/protected-route';
import { LayoutWrapper } from '@/components/layout-wrapper';
import { useState, useEffect } from 'react';
import { FileText, Calendar, Tag } from 'lucide-react';

interface ReleaseNote {
  id: string;
  version: string;
  title: string;
  description: string;
  changes: Array<{
    type: 'added' | 'changed' | 'fixed' | 'removed' | 'security';
    items: string[];
  }>;
  releaseDate: string;
  type: 'major' | 'minor' | 'patch';
  isPublished: boolean;
}

export default function ReleaseNotesPage() {
  const [releases, setReleases] = useState<ReleaseNote[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadReleases();
  }, []);

  const loadReleases = async () => {
    try {
      const response = await fetch('/api/release-notes');
      const data = await response.json();
      if (data.success) {
        setReleases(data.data);
      }
    } catch (error) {
      console.error('Error loading release notes:', error);
    } finally {
      setLoading(false);
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'major':
        return 'bg-red-100 text-red-800';
      case 'minor':
        return 'bg-blue-100 text-blue-800';
      case 'patch':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getChangeTypeColor = (type: string) => {
    switch (type) {
      case 'added':
        return 'text-green-700';
      case 'changed':
        return 'text-blue-700';
      case 'fixed':
        return 'text-orange-700';
      case 'removed':
        return 'text-red-700';
      case 'security':
        return 'text-purple-700';
      default:
        return 'text-gray-700';
    }
  };

  const getChangeTypeIcon = (type: string) => {
    switch (type) {
      case 'added':
        return '✨';
      case 'changed':
        return '🔄';
      case 'fixed':
        return '🐛';
      case 'removed':
        return '🗑️';
      case 'security':
        return '🔒';
      default:
        return '📝';
    }
  };

  if (loading) {
    return (
      <ProtectedRoute>
        <LayoutWrapper>
          <div className="min-h-screen flex items-center justify-center">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Loading release notes...</p>
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
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* Header */}
            <div className="mb-8">
              <div className="flex items-center gap-3 mb-2">
                <FileText className="h-8 w-8 text-blue-600" />
                <h1 className="text-3xl font-bold text-gray-900">Release Notes</h1>
              </div>
              <p className="text-gray-600">
                Stay updated with the latest features, improvements, and fixes
              </p>
            </div>

            {/* Release Notes List */}
            {releases.length === 0 ? (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
                <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Release Notes Yet</h3>
                <p className="text-gray-600">Release notes will appear here when published.</p>
              </div>
            ) : (
              <div className="space-y-8">
                {releases.map((release) => (
                  <div key={release.id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    {/* Release Header */}
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center space-x-3">
                        <h2 className="text-2xl font-bold text-gray-900">v{release.version}</h2>
                        <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getTypeColor(release.type)}`}>
                          {release.type.toUpperCase()}
                        </span>
                      </div>
                      <div className="flex items-center text-sm text-gray-500">
                        <Calendar className="h-4 w-4 mr-1" />
                        {new Date(release.releaseDate).toLocaleDateString('en-US', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric',
                        })}
                      </div>
                    </div>

                    <h3 className="text-lg font-semibold text-gray-800 mb-2">{release.title}</h3>
                    <p className="text-gray-600 mb-6">{release.description}</p>

                    {/* Changes */}
                    <div className="space-y-4">
                      {release.changes.map((change, idx) => (
                        <div key={idx}>
                          <h4 className={`text-sm font-semibold uppercase mb-2 flex items-center gap-2 ${getChangeTypeColor(change.type)}`}>
                            <span>{getChangeTypeIcon(change.type)}</span>
                            {change.type}
                          </h4>
                          <ul className="space-y-1 ml-6">
                            {change.items.map((item, itemIdx) => (
                              <li key={itemIdx} className="text-sm text-gray-700 list-disc">
                                {item}
                              </li>
                            ))}
                          </ul>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Footer */}
            <div className="mt-12 text-center">
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">🔔 Stay Updated</h3>
                <p className="text-gray-600 mb-4">
                  Want to be notified about new releases? Contact your administrator to be added to the update notifications.
                </p>
                <div className="text-sm text-gray-500">
                  <p>Last Updated: {new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </LayoutWrapper>
    </ProtectedRoute>
  );
}
