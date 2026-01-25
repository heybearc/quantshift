"use client";

import { useAuth } from "@/lib/auth-context";
import { Navigation } from "@/components/navigation";
import { ReleaseBanner } from "@/components/release-banner";
import { useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import { Monitor, Trash2, RefreshCw, Loader2 } from "lucide-react";

interface Session {
  id: string;
  userId: string;
  token: string;
  ipAddress: string | null;
  userAgent: string | null;
  expiresAt: string;
  createdAt: string;
  user: {
    email: string;
    fullName: string | null;
    role: string;
  };
}

export default function SessionsPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState<string | null>(null);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login");
    }
    if (!authLoading && user && user.role?.toUpperCase() !== "ADMIN") {
      router.push("/dashboard");
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    if (user?.role?.toUpperCase() === "ADMIN") {
      loadSessions();
    }
  }, [user]);

  const loadSessions = async () => {
    try {
      setLoading(true);
      const response = await fetch("/api/admin/sessions", {
        credentials: "include",
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success && data.data) {
          setSessions(data.data);
        }
      }
    } catch (error) {
      console.error("Error loading sessions:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleRevokeSession = async (sessionId: string) => {
    if (!confirm("Are you sure you want to revoke this session?")) {
      return;
    }

    setProcessing(sessionId);
    setMessage(null);

    try {
      const response = await fetch(`/api/admin/sessions/${sessionId}`, {
        method: "DELETE",
        credentials: "include",
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setMessage({ type: "success", text: "Session revoked successfully" });
        loadSessions();
      } else {
        setMessage({ type: "error", text: data.error || "Failed to revoke session" });
      }
    } catch (error) {
      setMessage({ type: "error", text: "Failed to revoke session" });
    } finally {
      setProcessing(null);
    }
  };

  if (authLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-900">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500"></div>
      </div>
    );
  }

  if (!user || user.role?.toUpperCase() !== "ADMIN") {
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
                <h1 className="text-3xl font-bold text-white">Session Management</h1>
                <p className="text-slate-400 mt-2">Monitor and manage active user sessions</p>
              </div>
              <button
                onClick={loadSessions}
                className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
              >
                <RefreshCw className="h-4 w-4" />
                Refresh
              </button>
            </div>

            {message && (
              <div
                className={`p-4 rounded-xl border ${
                  message.type === "success"
                    ? "bg-green-900/20 border-green-700 text-green-400"
                    : "bg-red-900/20 border-red-700 text-red-400"
                }`}
              >
                {message.text}
              </div>
            )}

            <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 overflow-hidden">
              {sessions.length === 0 ? (
                <div className="p-12 text-center">
                  <Monitor className="h-12 w-12 text-slate-600 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-white mb-2">No Active Sessions</h3>
                  <p className="text-slate-400">Active user sessions will appear here</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-slate-900/50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                          User
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                          Role
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                          IP Address
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                          Created
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                          Expires
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-700">
                      {sessions.map((session) => (
                        <tr key={session.id} className="hover:bg-slate-800/50 transition-colors">
                          <td className="px-6 py-4">
                            <div>
                              <div className="text-sm font-medium text-white">
                                {session.user.fullName || "No name"}
                              </div>
                              <div className="text-sm text-slate-400">{session.user.email}</div>
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-cyan-900/50 text-cyan-300">
                              {session.user.role}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-sm text-slate-400">
                            {session.ipAddress || "Unknown"}
                          </td>
                          <td className="px-6 py-4 text-sm text-slate-400">
                            {new Date(session.createdAt).toLocaleString()}
                          </td>
                          <td className="px-6 py-4 text-sm text-slate-400">
                            {new Date(session.expiresAt).toLocaleString()}
                          </td>
                          <td className="px-6 py-4">
                            <button
                              onClick={() => handleRevokeSession(session.id)}
                              disabled={processing === session.id}
                              className="flex items-center gap-1 px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white text-xs rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                              {processing === session.id ? (
                                <Loader2 className="h-3 w-3 animate-spin" />
                              ) : (
                                <Trash2 className="h-3 w-3" />
                              )}
                              Revoke
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            <div className="bg-blue-900/20 border border-blue-700 rounded-xl p-4">
              <p className="text-sm text-blue-300">
                <strong>Note:</strong> You are currently viewing {sessions.length} active session{sessions.length !== 1 ? 's' : ''}. 
                Revoking a session will immediately log out that user.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
