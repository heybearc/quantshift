'use client';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Navigation } from '@/components/navigation';
import { useAuth } from '@/lib/auth-context';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { Sparkles, Calendar, Tag, ChevronDown, ChevronUp } from 'lucide-react';

interface ReleaseNote {
  version: string;
  date: string;
  type: 'major' | 'minor' | 'patch';
  content: string;
  slug: string;
}

export default function ReleaseNotesPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [releaseNotes, setReleaseNotes] = useState<ReleaseNote[]>([]);
  const [dataLoading, setDataLoading] = useState(true);
  const [expandedVersions, setExpandedVersions] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login');
    }
  }, [user, loading, router]);

  useEffect(() => {
    if (user) {
      fetchReleaseNotes();
    }
  }, [user]);

  const fetchReleaseNotes = async () => {
    try {
      const response = await fetch('/api/release-notes/all');
      if (response.ok) {
        const data = await response.json();
        setReleaseNotes(data);
        // Auto-expand latest version
        if (data.length > 0) {
          setExpandedVersions(new Set([data[0].version]));
        }
      }
    } catch (error) {
      console.error('Error fetching release notes:', error);
    } finally {
      setDataLoading(false);
    }
  };

  const toggleVersion = (version: string) => {
    const newExpanded = new Set(expandedVersions);
    if (newExpanded.has(version)) {
      newExpanded.delete(version);
    } else {
      newExpanded.add(version);
    }
    setExpandedVersions(newExpanded);
  };

  const getTypeBadge = (type: string) => {
    switch (type) {
      case 'major':
        return {
          color: 'bg-red-500/10 text-red-400 border-red-500/30',
          icon: '🚀',
          label: 'Major Release'
        };
      case 'minor':
        return {
          color: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
          icon: '✨',
          label: 'New Features'
        };
      case 'patch':
        return {
          color: 'bg-green-500/10 text-green-400 border-green-500/30',
          icon: '🔧',
          label: 'Bug Fixes'
        };
      default:
        return {
          color: 'bg-slate-500/10 text-slate-400 border-slate-500/30',
          icon: '📦',
          label: 'Update'
        };
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const getRelativeTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`;
    return `${Math.floor(diffDays / 365)} years ago`;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-900">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500"></div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="flex h-screen bg-slate-900">
      <Navigation />
      <main className="flex-1 lg:ml-64 overflow-y-auto">
        <div className="p-8">
          <div className="max-w-5xl mx-auto">
            {/* Header */}
            <div className="mb-10">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 bg-gradient-to-br from-cyan-500/20 to-blue-500/20 rounded-lg border border-cyan-500/30">
                  <Sparkles className="h-6 w-6 text-cyan-400" />
                </div>
                <h1 className="text-4xl font-bold text-white">
                  Release Notes
                </h1>
              </div>
              <p className="text-lg text-slate-400">
                Stay up to date with new features, improvements, and bug fixes
              </p>
              {releaseNotes.length > 0 && (
                <div className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-cyan-500/10 border border-cyan-500/30 rounded-lg">
                  <span className="text-sm font-medium text-cyan-400">Latest:</span>
                  <span className="text-sm text-white font-semibold">v{releaseNotes[0].version}</span>
                  <span className="text-sm text-slate-400">•</span>
                  <span className="text-sm text-slate-400">{getRelativeTime(releaseNotes[0].date)}</span>
                </div>
              )}
            </div>

            {dataLoading ? (
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500"></div>
              </div>
            ) : releaseNotes.length === 0 ? (
              <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-12 text-center border border-slate-700">
                <Sparkles className="h-12 w-12 text-slate-600 mx-auto mb-4" />
                <p className="text-slate-400 text-lg">No release notes available yet.</p>
              </div>
            ) : (
              <div className="relative">
                {/* Timeline line */}
                <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-gradient-to-b from-cyan-500/50 via-blue-500/30 to-transparent"></div>

                <div className="space-y-8">
                  {releaseNotes.map((note, index) => {
                    const badge = getTypeBadge(note.type);
                    const isExpanded = expandedVersions.has(note.version);
                    const isLatest = index === 0;

                    return (
                      <div key={note.version} className="relative pl-20">
                        {/* Timeline dot */}
                        <div className={`absolute left-6 top-6 w-5 h-5 rounded-full border-4 ${
                          isLatest 
                            ? 'bg-cyan-500 border-cyan-400 shadow-lg shadow-cyan-500/50' 
                            : 'bg-slate-700 border-slate-600'
                        }`}></div>

                        <div className={`bg-slate-800/50 backdrop-blur-sm rounded-xl border overflow-hidden transition-all ${
                          isLatest 
                            ? 'border-cyan-500/50 shadow-lg shadow-cyan-500/10' 
                            : 'border-slate-700'
                        }`}>
                          {/* Header - Always visible */}
                          <button
                            onClick={() => toggleVersion(note.version)}
                            className="w-full text-left px-6 py-5 hover:bg-slate-700/30 transition-colors"
                          >
                            <div className="flex items-start justify-between gap-4">
                              <div className="flex-1">
                                <div className="flex items-center gap-3 mb-2">
                                  <h2 className="text-2xl font-bold text-white">
                                    v{note.version}
                                  </h2>
                                  {isLatest && (
                                    <span className="px-2 py-1 bg-cyan-500/20 text-cyan-400 text-xs font-semibold rounded border border-cyan-500/30">
                                      LATEST
                                    </span>
                                  )}
                                </div>
                                <div className="flex items-center gap-4 text-sm">
                                  <div className="flex items-center gap-2">
                                    <Calendar className="h-4 w-4 text-slate-500" />
                                    <span className="text-slate-400">{formatDate(note.date)}</span>
                                    <span className="text-slate-600">•</span>
                                    <span className="text-slate-500">{getRelativeTime(note.date)}</span>
                                  </div>
                                  <div className="flex items-center gap-2">
                                    <Tag className="h-4 w-4 text-slate-500" />
                                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium border ${badge.color}`}>
                                      <span>{badge.icon}</span>
                                      <span>{badge.label}</span>
                                    </span>
                                  </div>
                                </div>
                              </div>
                              <div className="flex-shrink-0 pt-1">
                                {isExpanded ? (
                                  <ChevronUp className="h-5 w-5 text-slate-400" />
                                ) : (
                                  <ChevronDown className="h-5 w-5 text-slate-400" />
                                )}
                              </div>
                            </div>
                          </button>

                          {/* Content - Collapsible */}
                          {isExpanded && (
                            <div className="px-6 pb-6 border-t border-slate-700/50">
                              <div className="pt-6 prose prose-sm max-w-none prose-invert 
                                prose-headings:text-white prose-headings:font-semibold
                                prose-h2:text-xl prose-h2:mt-8 prose-h2:mb-4 prose-h2:pb-2 prose-h2:border-b prose-h2:border-slate-700
                                prose-h3:text-lg prose-h3:mt-6 prose-h3:mb-3
                                prose-p:text-slate-300 prose-p:leading-relaxed
                                prose-li:text-slate-300 prose-li:my-1
                                prose-strong:text-white prose-strong:font-semibold
                                prose-a:text-cyan-400 prose-a:no-underline hover:prose-a:text-cyan-300 hover:prose-a:underline
                                prose-code:text-cyan-400 prose-code:bg-slate-800 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded
                                prose-ul:my-4 prose-ol:my-4
                                prose-hr:border-slate-700 prose-hr:my-8">
                                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                  {note.content}
                                </ReactMarkdown>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
