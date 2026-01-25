"use client";

import { useAuth } from "@/lib/auth-context";
import { Navigation } from "@/components/navigation";
import { ReleaseBanner } from "@/components/release-banner";
import { useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import { Mail, Send, Clock, CheckCircle, XCircle, Loader2, UserPlus, RefreshCw } from "lucide-react";

interface Invitation {
  id: string;
  email: string;
  invitedByName: string;
  status: "PENDING" | "ACCEPTED" | "EXPIRED" | "CANCELLED";
  expiresAt: string;
  acceptedAt?: string;
  createdAt: string;
}

export default function InvitationsPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [loading, setLoading] = useState(true);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [email, setEmail] = useState("");
  const [sending, setSending] = useState(false);
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
      loadInvitations();
    }
  }, [user]);

  const loadInvitations = async () => {
    try {
      setLoading(true);
      const response = await fetch("/api/admin/users/invite", {
        credentials: "include",
      });
      const data = await response.json();

      if (data.success) {
        setInvitations(data.data || []);
      }
    } catch (error) {
      console.error("Error loading invitations:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSendInvitation = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage(null);
    setSending(true);

    try {
      const response = await fetch("/api/admin/users/invite", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email }),
      });

      const data = await response.json();

      if (data.success) {
        setMessage({ type: "success", text: `Invitation sent to ${email}` });
        setEmail("");
        setShowInviteModal(false);
        loadInvitations();
      } else {
        setMessage({ type: "error", text: data.error || "Failed to send invitation" });
      }
    } catch (error) {
      setMessage({ type: "error", text: "An error occurred while sending invitation" });
    } finally {
      setSending(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "PENDING":
        return <Clock className="h-5 w-5 text-yellow-400" />;
      case "ACCEPTED":
        return <CheckCircle className="h-5 w-5 text-green-400" />;
      case "EXPIRED":
        return <XCircle className="h-5 w-5 text-red-400" />;
      case "CANCELLED":
        return <XCircle className="h-5 w-5 text-slate-500" />;
      default:
        return null;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "PENDING":
        return "bg-yellow-900/50 text-yellow-300 border-yellow-700";
      case "ACCEPTED":
        return "bg-green-900/50 text-green-300 border-green-700";
      case "EXPIRED":
        return "bg-red-900/50 text-red-300 border-red-700";
      case "CANCELLED":
        return "bg-slate-800 text-slate-400 border-slate-700";
      default:
        return "bg-slate-800 text-slate-400 border-slate-700";
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
                <h1 className="text-3xl font-bold text-white">User Invitations</h1>
                <p className="text-slate-400 mt-2">Invite new users to the platform</p>
              </div>
              <button
                onClick={() => setShowInviteModal(true)}
                className="flex items-center gap-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg transition-colors"
              >
                <UserPlus className="h-4 w-4" />
                Send Invitation
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
              {invitations.length === 0 ? (
                <div className="p-12 text-center">
                  <Mail className="h-12 w-12 text-slate-600 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-white mb-2">No Invitations Yet</h3>
                  <p className="text-slate-400 mb-4">Send your first invitation to get started</p>
                  <button
                    onClick={() => setShowInviteModal(true)}
                    className="inline-flex items-center gap-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg transition-colors"
                  >
                    <Send className="h-4 w-4" />
                    Send Invitation
                  </button>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-slate-900/50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                          Email
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                          Status
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                          Invited By
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                          Sent
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                          Expires
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-700">
                      {invitations.map((invitation) => (
                        <tr key={invitation.id} className="hover:bg-slate-800/50 transition-colors">
                          <td className="px-6 py-4 text-sm text-white">{invitation.email}</td>
                          <td className="px-6 py-4">
                            <span
                              className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium border ${getStatusColor(
                                invitation.status
                              )}`}
                            >
                              {getStatusIcon(invitation.status)}
                              {invitation.status}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-sm text-slate-400">{invitation.invitedByName}</td>
                          <td className="px-6 py-4 text-sm text-slate-400">
                            {new Date(invitation.createdAt).toLocaleDateString()}
                          </td>
                          <td className="px-6 py-4 text-sm text-slate-400">
                            {new Date(invitation.expiresAt).toLocaleDateString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>

      {showInviteModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-xl border border-slate-700 p-6 w-full max-w-md mx-4">
            <h2 className="text-xl font-bold text-white mb-4">Send Invitation</h2>
            <form onSubmit={handleSendInvitation} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Email Address</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="user@example.com"
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                  required
                />
              </div>
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowInviteModal(false);
                    setEmail("");
                    setMessage(null);
                  }}
                  className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={sending}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {sending ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Sending...
                    </>
                  ) : (
                    <>
                      <Send className="h-4 w-4" />
                      Send
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
