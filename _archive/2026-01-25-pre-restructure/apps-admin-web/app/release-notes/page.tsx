'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

interface ReleaseNote {
  id: string;
  version: string;
  title: string;
  description: string;
  type: string;
  changes: Array<{
    type: string;
    description: string;
  }>;
  releaseDate: string;
}

function getTypeColor(type: string) {
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
}

function getTypeIcon(type: string) {
  switch (type) {
    case 'feature':
      return '✨';
    case 'fix':
      return '🐛';
    case 'improvement':
      return '🚀';
    default:
      return '📝';
  }
}

export default function ReleaseNotesPage() {
  const [releases, setReleases] = useState<ReleaseNote[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchReleases() {
      try {
        const response = await fetch('/api/release-notes', {
          credentials: 'include',
        });
        
        if (response.ok) {
          const data = await response.json();
          setReleases(data.data || []);
        }
      } catch (error) {
        console.error('Error fetching release notes:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchReleases();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center">
        <div className="text-gray-600">Loading release notes...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center space-x-3 mb-2">
                <div className="h-10 w-10 bg-white/20 backdrop-blur-sm rounded-lg flex items-center justify-center">
                  <span className="text-2xl">📋</span>
                </div>
                <h1 className="text-3xl font-bold">Release Notes</h1>
              </div>
              <p className="text-blue-100 ml-13">
                Stay updated with the latest features, improvements, and fixes
              </p>
            </div>
            <Link
              href="/dashboard"
              className="bg-white/10 hover:bg-white/20 backdrop-blur-sm text-white px-6 py-2.5 rounded-lg font-medium transition-all duration-200 border border-white/20"
            >
              ← Back to Dashboard
            </Link>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {releases.length === 0 ? (
          <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-8 text-center">
            <p className="text-yellow-800 text-lg">No release notes available yet.</p>
          </div>
        ) : (
          <div className="space-y-8">
            {releases.map((release) => (
              <div
                key={release.id}
                className="bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow duration-200 overflow-hidden border border-gray-100"
              >
                {/* Release Header */}
                <div className="bg-gradient-to-r from-gray-50 to-blue-50 px-8 py-6 border-b border-gray-200">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                    <div className="flex items-center space-x-3">
                      <h2 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                        v{release.version}
                      </h2>
                      <span
                        className={`px-3 py-1 text-xs font-bold rounded-full ${getTypeColor(
                          release.type
                        )} shadow-sm`}
                      >
                        {release.type.toUpperCase()}
                      </span>
                    </div>
                    <span className="text-sm font-medium text-gray-600 bg-white px-4 py-2 rounded-lg shadow-sm">
                      📅 {new Date(release.releaseDate).toLocaleDateString('en-US', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                      })}
                    </span>
                  </div>
                  <h3 className="text-xl font-bold text-gray-800 mt-4">{release.title}</h3>
                  <p className="text-gray-600 mt-2">{release.description}</p>
                </div>

                {/* Changes Content */}
                <div className="px-8 py-6">
                  {release.changes && release.changes.length > 0 && (
                    <div className="space-y-6">
                      {/* Group changes by type */}
                      {['feature', 'improvement', 'fix', 'other'].map((changeType) => {
                        const changesOfType = release.changes.filter(
                          (c) => c.type === changeType
                        );
                        if (changesOfType.length === 0) return null;

                        const sectionTitle =
                          changeType === 'feature'
                            ? '✨ New Features'
                            : changeType === 'improvement'
                            ? '🚀 Improvements'
                            : changeType === 'fix'
                            ? '🐛 Bug Fixes'
                            : '📝 Other Changes';

                        return (
                          <div key={changeType}>
                            <h4 className="text-lg font-bold text-gray-900 mb-3">
                              {sectionTitle}
                            </h4>
                            <ul className="space-y-2">
                              {changesOfType.map((change, idx) => (
                                <li
                                  key={idx}
                                  className="flex items-start space-x-2 text-gray-700"
                                >
                                  <span className="text-blue-600 mt-1">•</span>
                                  <span>{change.description}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Footer CTA */}
        <div className="mt-16">
          <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl shadow-lg p-8 text-center text-white">
            <div className="text-4xl mb-4">🔔</div>
            <h3 className="text-2xl font-bold mb-3">Stay Updated</h3>
            <p className="text-blue-100 mb-6 max-w-2xl mx-auto">
              Check back regularly for new features, improvements, and bug fixes to the
              QuantShift platform.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <Link
                href="/dashboard"
                className="bg-white text-blue-600 hover:bg-blue-50 px-6 py-3 rounded-lg font-semibold transition-colors duration-200 shadow-md"
              >
                🏠 Back to Dashboard
              </Link>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
