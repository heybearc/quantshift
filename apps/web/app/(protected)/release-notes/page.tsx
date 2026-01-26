'use client';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Navigation } from '@/components/navigation';
import { useAuth } from '@/lib/auth-context';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

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
      }
    } catch (error) {
      console.error('Error fetching release notes:', error);
    } finally {
      setDataLoading(false);
    }
  };

  const getTypeBadgeColor = (type: string) => {
    switch (type) {
      case 'major':
        return 'bg-red-900/50 text-red-300 border-red-700';
      case 'minor':
        return 'bg-blue-900/50 text-blue-300 border-blue-700';
      case 'patch':
        return 'bg-green-900/50 text-green-300 border-green-700';
      default:
        return 'bg-slate-800/50 text-slate-300 border-slate-700';
    }
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
          <div className="max-w-4xl mx-auto">
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-white mb-2">
                Release Notes
              </h1>
              <p className="text-slate-400">
                Track new features, improvements, and bug fixes in QuantShift
              </p>
            </div>

            {dataLoading ? (
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500"></div>
              </div>
            ) : releaseNotes.length === 0 ? (
              <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-8 text-center border border-slate-700">
                <p className="text-slate-400">No release notes available yet.</p>
              </div>
            ) : (
              <div className="space-y-6">
                {releaseNotes.map((note) => (
                  <div
                    key={note.version}
                    className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 overflow-hidden"
                  >
                    <div className="bg-gradient-to-r from-slate-800/80 to-slate-800/50 px-6 py-4 border-b border-slate-700">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <h2 className="text-2xl font-bold text-white">
                            v{note.version}
                          </h2>
                          <span
                            className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border ${getTypeBadgeColor(
                              note.type
                            )}`}
                          >
                            {note.type.charAt(0).toUpperCase() + note.type.slice(1)}
                          </span>
                        </div>
                        <time className="text-sm text-slate-400">
                          {new Date(note.date).toLocaleDateString('en-US', {
                            year: 'numeric',
                            month: 'long',
                            day: 'numeric',
                          })}
                        </time>
                      </div>
                    </div>

                    <div className="px-6 py-6">
                      <div className="prose prose-sm max-w-none prose-invert prose-headings:text-white prose-p:text-slate-300 prose-li:text-slate-300 prose-strong:text-white prose-a:text-cyan-400 hover:prose-a:text-cyan-300">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {note.content}
                        </ReactMarkdown>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
