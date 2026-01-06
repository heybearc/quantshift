"use client";

import { useEffect, useState } from "react";
import { Navigation } from "@/components/navigation";
import { ReleaseBanner } from "@/components/release-banner";
import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";
import { Sparkles, Calendar, Tag } from "lucide-react";

interface ReleaseNote {
  id: string;
  version: string;
  title: string;
  description: string;
  releaseDate: string;
  features: string[];
  bugFixes: string[];
  improvements: string[];
}

export default function ReleaseNotesPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [releaseNotes, setReleaseNotes] = useState<ReleaseNote[]>([]);
  const [dataLoading, setDataLoading] = useState(true);

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
  }, [user, loading, router]);

  useEffect(() => {
    if (user) {
      loadReleaseNotes();
    }
  }, [user]);

  const loadReleaseNotes = async () => {
    try {
      const response = await fetch("/api/release-notes");
      if (response.ok) {
        const data = await response.json();
        setReleaseNotes(data);
      }
    } catch (error) {
      console.error("Failed to load release notes:", error);
    } finally {
      setDataLoading(false);
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
        {user && <ReleaseBanner userId={user.id} />}
        <div className="p-8">
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-white">Release Notes</h1>
                <p className="text-slate-400 mt-2">Latest updates and improvements</p>
              </div>
              <Sparkles className="h-8 w-8 text-cyan-500" />
            </div>

            {dataLoading ? (
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500"></div>
              </div>
            ) : releaseNotes.length === 0 ? (
              <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-12 text-center">
                <Sparkles className="h-12 w-12 text-slate-600 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-white mb-2">No Release Notes Yet</h3>
                <p className="text-slate-400">Check back soon for updates and new features!</p>
              </div>
            ) : (
              <div className="space-y-6">
                {releaseNotes.map((note) => (
                  <div
                    key={note.id}
                    className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6"
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <div className="flex items-center gap-3 mb-2">
                          <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium bg-cyan-900/50 text-cyan-300">
                            <Tag className="h-3 w-3" />
                            v{note.version}
                          </span>
                          <h2 className="text-xl font-bold text-white">{note.title}</h2>
                        </div>
                        <p className="text-slate-400">{note.description}</p>
                      </div>
                      <div className="flex items-center gap-2 text-slate-400 text-sm">
                        <Calendar className="h-4 w-4" />
                        {new Date(note.releaseDate).toLocaleDateString()}
                      </div>
                    </div>

                    {note.features && note.features.length > 0 && (
                      <div className="mb-4">
                        <h3 className="text-sm font-semibold text-green-400 mb-2">✨ New Features</h3>
                        <ul className="space-y-1">
                          {note.features.map((feature, idx) => (
                            <li key={idx} className="text-sm text-slate-300 pl-4">
                              • {feature}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {note.improvements && note.improvements.length > 0 && (
                      <div className="mb-4">
                        <h3 className="text-sm font-semibold text-blue-400 mb-2">🔧 Improvements</h3>
                        <ul className="space-y-1">
                          {note.improvements.map((improvement, idx) => (
                            <li key={idx} className="text-sm text-slate-300 pl-4">
                              • {improvement}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {note.bugFixes && note.bugFixes.length > 0 && (
                      <div>
                        <h3 className="text-sm font-semibold text-red-400 mb-2">🐛 Bug Fixes</h3>
                        <ul className="space-y-1">
                          {note.bugFixes.map((fix, idx) => (
                            <li key={idx} className="text-sm text-slate-300 pl-4">
                              • {fix}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
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
