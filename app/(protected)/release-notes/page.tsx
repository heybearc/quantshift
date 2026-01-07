"use client";

import { ProtectedRoute } from "@/components/protected-route";
import { LayoutWrapper } from "@/components/layout-wrapper";
import { useEffect, useState } from "react";
import Link from "next/link";

interface ReleaseNote {
  id: string;
  version: string;
  title: string;
  description: string;
  type: string;
  changes: any;
  releaseDate: string;
}

function getTypeColor(type: string) {
  switch (type) {
    case "major":
      return "bg-red-900/20 text-red-400 border-red-700";
    case "minor":
      return "bg-blue-900/20 text-blue-400 border-blue-700";
    case "patch":
      return "bg-green-900/20 text-green-400 border-green-700";
    default:
      return "bg-slate-700 text-slate-300 border-slate-600";
  }
}

export default function ReleaseNotesPage() {
  return (
    <ProtectedRoute>
      <LayoutWrapper>
        <ReleaseNotesContent />
      </LayoutWrapper>
    </ProtectedRoute>
  );
}

function ReleaseNotesContent() {
  const [releases, setReleases] = useState<ReleaseNote[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchReleases() {
      try {
        const response = await fetch("/api/release-notes", {
          credentials: "include",
        });

        if (response.ok) {
          const data = await response.json();
          setReleases(data.data || []);
        }
      } catch (error) {
        console.error("Error fetching release notes:", error);
      } finally {
        setLoading(false);
      }
    }

    fetchReleases();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500"></div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="h-10 w-10 bg-cyan-600/20 rounded-lg flex items-center justify-center">
                <span className="text-2xl">📋</span>
              </div>
              <h1 className="text-3xl font-bold text-white">Release Notes</h1>
            </div>
            <p className="text-slate-400">Stay updated with the latest features, improvements, and fixes</p>
          </div>
          <Link
            href="/dashboard"
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
          >
            ← Back to Dashboard
          </Link>
        </div>

        {releases.length === 0 ? (
          <div className="bg-yellow-900/20 border border-yellow-700 rounded-xl p-8 text-center">
            <p className="text-yellow-400 text-lg">No release notes available yet.</p>
          </div>
        ) : (
          <div className="space-y-8">
            {releases.map((release) => {
              const changes = typeof release.changes === "string" ? JSON.parse(release.changes) : release.changes;
              const features = changes?.features || [];
              const improvements = changes?.improvements || [];
              const bugFixes = changes?.bugFixes || [];

              return (
                <div
                  key={release.id}
                  className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 overflow-hidden"
                >
                  <div className="bg-gradient-to-r from-slate-800 to-slate-700 px-8 py-6 border-b border-slate-600">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                      <div className="flex items-center gap-3">
                        <h2 className="text-3xl font-bold text-white">v{release.version}</h2>
                        <span className={`px-3 py-1 text-xs font-bold rounded-full border ${getTypeColor(release.type)}`}>
                          {release.type.toUpperCase()}
                        </span>
                      </div>
                      <span className="text-sm font-medium text-slate-400">
                        📅{" "}
                        {new Date(release.releaseDate).toLocaleDateString("en-US", {
                          year: "numeric",
                          month: "long",
                          day: "numeric",
                        })}
                      </span>
                    </div>
                    <h3 className="text-xl font-bold text-white mt-4">{release.title}</h3>
                    <p className="text-slate-300 mt-2">{release.description}</p>
                  </div>

                  <div className="px-8 py-6 space-y-6">
                    {features.length > 0 && (
                      <div>
                        <h4 className="text-lg font-bold text-white mb-3 flex items-center gap-2">
                          <span>✨</span>
                          <span>New Features</span>
                        </h4>
                        <ul className="space-y-2">
                          {features.map((feature: string, idx: number) => (
                            <li key={idx} className="flex items-start gap-2 text-slate-300">
                              <span className="text-cyan-400 mt-1">•</span>
                              <span>{feature}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {improvements.length > 0 && (
                      <div>
                        <h4 className="text-lg font-bold text-white mb-3 flex items-center gap-2">
                          <span>🚀</span>
                          <span>Improvements</span>
                        </h4>
                        <ul className="space-y-2">
                          {improvements.map((improvement: string, idx: number) => (
                            <li key={idx} className="flex items-start gap-2 text-slate-300">
                              <span className="text-cyan-400 mt-1">•</span>
                              <span>{improvement}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {bugFixes.length > 0 && (
                      <div>
                        <h4 className="text-lg font-bold text-white mb-3 flex items-center gap-2">
                          <span>🐛</span>
                          <span>Bug Fixes</span>
                        </h4>
                        <ul className="space-y-2">
                          {bugFixes.map((fix: string, idx: number) => (
                            <li key={idx} className="flex items-start gap-2 text-slate-300">
                              <span className="text-cyan-400 mt-1">•</span>
                              <span>{fix}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        <div className="mt-16">
          <div className="bg-gradient-to-r from-cyan-600 to-blue-600 rounded-xl p-8 text-center text-white">
            <div className="text-4xl mb-4">🔔</div>
            <h3 className="text-2xl font-bold mb-3">Stay Updated</h3>
            <p className="text-blue-100 mb-6 max-w-2xl mx-auto">
              Check back regularly for new features, improvements, and bug fixes to the QuantShift platform.
            </p>
            <Link
              href="/dashboard"
              className="inline-block bg-white text-blue-600 hover:bg-blue-50 px-6 py-3 rounded-lg font-semibold transition-colors"
            >
              🏠 Back to Dashboard
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
