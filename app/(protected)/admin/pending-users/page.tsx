"use client";

import { useAuth } from "@/lib/auth-context";
import { Navigation } from "@/components/navigation";
import { ReleaseBanner } from "@/components/release-banner";
import { useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import { UserCheck, UserX, Clock, Mail, User, Loader2, RefreshCw, CheckCircle, XCircle } from "lucide-react";

interface PendingUser {
  id: string;
  email: string;
  username: string;
  fullName: string;
  accountStatus: string;
  createdAt: string;
  emailVerified: boolean;
}

export default function PendingUsersPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [users, setUsers] = useState<PendingUser[]>([]);
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
      loadPendingUsers();
    }
  }, [user]);

  const loadPendingUsers = async () => {
    try {
      setLoading(true);
      const response = await fetch("/api/users", {
        credentials: "include",
      });
      const data = await response.json();

      if (data.success) {
        const pending = data.users.filter(
          (u: any) => u.accountStatus === "PENDING_APPROVAL"
        );
        setUsers(pending);
      }
    } catch (error) {
      console.error("Error loading pending users:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (userId: string) => {
    setProcessing(userId);
    setMessage(null);

    try {
      const response = await fetch(`/api/users/${userId}/approve`, {
        method: "POST",
        credentials: "include",
      });

      const data = await response.json();

      if (data.success) {
        setMessage({ type: "success", text: "User approved successfully" });
        loadPendingUsers();
      } else {
        setMessage({ type: "error", text: data.error || "Failed to approve user" });
      }
    } catch (error) {
      setMessage({ type: "error", text: "An error occurred while approving user" });
    } finally {
      setProcessing(null);
    }
  };

  const handleReject = async (userId: string) => {
    if (!confirm("Are you sure you want to reject this user?")) {
      return;
    }

    setProcessing(userId);
    setMessage(null);

    try {
      const response = await fetch(`/api/users/${userId}`, {
        method: "DELETE",
        credentials: "include",
      });

      const data = await response.json();

      if (data.success) {
        setMessage({ type: "success", text: "User rejected successfully" });
        loadPendingUsers();
      } else {
        setMessage({ type: "error", text: data.error || "Failed to reject user" });
      }
    } catch (error) {
      setMessage({ type: "error", text: "An error occurred while rejecting user" });
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
                <h1 className="text-3xl font-bold text-white">Pending Approvals</h1>
                <p className="text-slate-400 mt-2">Review and approve new user registrations</p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={loadPendingUsers}
                  className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
                >
                  <RefreshCw className="h-4 w-4" />
                  Refresh
                </button>
              </div>
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
              {users.length === 0 ? (
                <div className="p-12 text-center">
                  <UserCheck className="h-12 w-12 text-slate-600 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-white mb-2">No Pending Approvals</h3>
                  <p className="text-slate-400">All user registrations have been processed</p>
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
                          Username
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                          Email Verified
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                          Registered
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-700">
                      {users.map((pendingUser) => (
                        <tr key={pendingUser.id} className="hover:bg-slate-800/50 transition-colors">
                          <td className="px-6 py-4">
                            <div>
                              <div className="text-sm font-medium text-white">
                                {pendingUser.fullName || "No name"}
                              </div>
                              <div className="text-sm text-slate-400">{pendingUser.email}</div>
                            </div>
                          </td>
                          <td className="px-6 py-4 text-sm text-slate-300">{pendingUser.username}</td>
                          <td className="px-6 py-4">
                            {pendingUser.emailVerified ? (
                              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-900/50 text-green-300">
                                <CheckCircle className="h-3 w-3" />
                                Verified
                              </span>
                            ) : (
                              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-900/50 text-yellow-300">
                                <Clock className="h-3 w-3" />
                                Pending
                              </span>
                            )}
                          </td>
                          <td className="px-6 py-4 text-sm text-slate-400">
                            {new Date(pendingUser.createdAt).toLocaleDateString()}
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => handleApprove(pendingUser.id)}
                                disabled={processing === pendingUser.id}
                                className="flex items-center gap-1 px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white text-sm rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                              >
                                {processing === pendingUser.id ? (
                                  <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                  <UserCheck className="h-4 w-4" />
                                )}
                                Approve
                              </button>
                              <button
                                onClick={() => handleReject(pendingUser.id)}
                                disabled={processing === pendingUser.id}
                                className="flex items-center gap-1 px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white text-sm rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                              >
                                <UserX className="h-4 w-4" />
                                Reject
                              </button>
                            </div>
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
    </div>
  );
}
