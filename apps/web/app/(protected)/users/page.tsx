"use client";

import { useEffect, useState } from "react";
import { Navigation } from "@/components/navigation";
import { ReleaseBanner } from "@/components/release-banner";
import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";
import { 
  Users, Search, Shield, CheckCircle, XCircle, Edit, Trash2, UserCheck, UserX, 
  UserPlus, Loader2, Phone, Mail, AlertCircle, Key, Lock
} from "lucide-react";

interface UserData {
  id: string;
  email: string;
  username: string;
  fullName: string | null;
  phoneNumber?: string | null;
  timeZone?: string | null;
  role: string;
  isActive: boolean;
  accountStatus: string;
  emailVerified: boolean;
  phoneVerified: boolean;
  mfaEnabled: boolean;
  requiresApproval: boolean;
  kycStatus: string;
  alpacaAccountId?: string | null;
  riskTolerance?: string | null;
  canPlaceOrders: boolean;
  subscriptionTier?: string | null;
  createdAt: string;
  lastLogin?: string | null;
}

interface NewUserForm {
  email: string;
  username: string;
  fullName: string;
  phoneNumber?: string;
  timeZone?: string;
  role: string;
  accountStatus: string;
  kycStatus: string;
  riskTolerance?: string;
  canPlaceOrders: boolean;
  subscriptionTier?: string;
  password: string;
}

export default function UsersPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [users, setUsers] = useState<UserData[]>([]);
  const [dataLoading, setDataLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [processing, setProcessing] = useState<string | null>(null);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  
  // Add User Modal
  const [showAddModal, setShowAddModal] = useState(false);
  const [newUser, setNewUser] = useState<NewUserForm>({
    email: "",
    username: "",
    fullName: "",
    phoneNumber: "",
    timeZone: "America/New_York",
    role: "VIEWER",
    accountStatus: "ACTIVE",
    kycStatus: "NOT_STARTED",
    riskTolerance: "MODERATE",
    canPlaceOrders: false,
    subscriptionTier: "FREE",
    password: ""
  });
  
  // Edit User Modal
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingUser, setEditingUser] = useState<UserData | null>(null);

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
    if (!loading && user && user.role?.toUpperCase() !== "ADMIN") {
      router.push("/dashboard");
    }
  }, [user, loading, router]);

  useEffect(() => {
    if (user?.role?.toUpperCase() === "ADMIN") {
      fetchUsers();
    }
  }, [user]);

  async function fetchUsers() {
    try {
      const response = await fetch("/api/users");
      if (response.ok) {
        const data = await response.json();
        setUsers(data.users || []);
      }
    } catch (error) {
      console.error("Failed to fetch users:", error);
      setUsers([]);
    } finally {
      setDataLoading(false);
    }
  }

  const handleAddUser = async () => {
    if (!newUser.email || !newUser.username || !newUser.fullName || !newUser.password) {
      setMessage({ type: "error", text: "Please fill in all required fields" });
      return;
    }

    setProcessing("add");
    setMessage(null);

    try {
      const response = await fetch("/api/users", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newUser),
      });

      const data = await response.json();

      if (response.ok) {
        setMessage({ type: "success", text: "User created successfully" });
        setShowAddModal(false);
        setNewUser({
          email: "",
          username: "",
          fullName: "",
          phoneNumber: "",
          timeZone: "America/New_York",
          role: "VIEWER",
          accountStatus: "ACTIVE",
          kycStatus: "NOT_STARTED",
          riskTolerance: "MODERATE",
          canPlaceOrders: false,
          subscriptionTier: "FREE",
          password: ""
        });
        fetchUsers();
      } else {
        setMessage({ type: "error", text: data.error || "Failed to create user" });
      }
    } catch (error) {
      setMessage({ type: "error", text: "An error occurred while creating user" });
    } finally {
      setProcessing(null);
    }
  };

  const handleEditUser = async () => {
    if (!editingUser || !editingUser.fullName || !editingUser.username) {
      setMessage({ type: "error", text: "Please fill in all required fields" });
      return;
    }

    setProcessing(editingUser.id);
    setMessage(null);

    try {
      const response = await fetch(`/api/users/${editingUser.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(editingUser),
      });

      const data = await response.json();

      if (response.ok) {
        setMessage({ type: "success", text: "User updated successfully" });
        setShowEditModal(false);
        setEditingUser(null);
        fetchUsers();
      } else {
        setMessage({ type: "error", text: data.error || "Failed to update user" });
      }
    } catch (error) {
      setMessage({ type: "error", text: "An error occurred while updating user" });
    } finally {
      setProcessing(null);
    }
  };

  const handleToggleActive = async (userId: string, currentStatus: boolean) => {
    setProcessing(userId);
    setMessage(null);

    try {
      const response = await fetch(`/api/users/${userId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ isActive: !currentStatus }),
      });

      const data = await response.json();

      if (response.ok) {
        setMessage({ 
          type: "success", 
          text: `User ${!currentStatus ? "activated" : "deactivated"} successfully` 
        });
        fetchUsers();
      } else {
        setMessage({ type: "error", text: data.error || "Failed to update user" });
      }
    } catch (error) {
      setMessage({ type: "error", text: "An error occurred while updating user" });
    } finally {
      setProcessing(null);
    }
  };

  const handleDeleteUser = async (userId: string, userEmail: string) => {
    if (!confirm(`Are you sure you want to delete user ${userEmail}?`)) {
      return;
    }

    setProcessing(userId);
    setMessage(null);

    try {
      const response = await fetch(`/api/users/${userId}`, {
        method: "DELETE",
      });

      const data = await response.json();

      if (response.ok) {
        setMessage({ type: "success", text: "User deleted successfully" });
        fetchUsers();
      } else {
        setMessage({ type: "error", text: data.error || "Failed to delete user" });
      }
    } catch (error) {
      setMessage({ type: "error", text: "An error occurred while deleting user" });
    } finally {
      setProcessing(null);
    }
  };

  const filteredUsers = users.filter(
    (u) =>
      u.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      u.fullName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      u.username?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
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
                <h1 className="text-3xl font-bold text-white">User Management</h1>
                <p className="text-slate-400 mt-2">Manage platform users and permissions</p>
              </div>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2 text-slate-400">
                  <Users className="h-5 w-5" />
                  <span className="text-sm">{users.length} total users</span>
                </div>
                <button
                  onClick={() => setShowAddModal(true)}
                  className="flex items-center gap-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg transition-colors"
                >
                  <UserPlus className="h-4 w-4" />
                  Add User
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

            <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search users by email, name, or username..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                />
              </div>
            </div>

            {dataLoading ? (
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500"></div>
              </div>
            ) : (
              <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 overflow-hidden">
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
                          Role
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                          Status
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                          Verification
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                          Last Login
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-700">
                      {filteredUsers.length === 0 ? (
                        <tr>
                          <td colSpan={7} className="px-6 py-8 text-center text-slate-400">
                            No users found
                          </td>
                        </tr>
                      ) : (
                        filteredUsers.map((u) => (
                          <tr key={u.id} className="hover:bg-slate-800/50 transition-colors">
                            <td className="px-6 py-4">
                              <div>
                                <div className="text-sm font-medium text-white">
                                  {u.fullName || "No name"}
                                </div>
                                <div className="text-sm text-slate-400">{u.email}</div>
                              </div>
                            </td>
                            <td className="px-6 py-4 text-sm text-slate-300">
                              {u.username}
                            </td>
                            <td className="px-6 py-4">
                              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-cyan-900/50 text-cyan-300">
                                <Shield className="h-3 w-3" />
                                {u.role}
                              </span>
                            </td>
                            <td className="px-6 py-4">
                              {u.isActive ? (
                                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-900/50 text-green-300">
                                  <CheckCircle className="h-3 w-3" />
                                  Active
                                </span>
                              ) : (
                                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-900/50 text-red-300">
                                  <XCircle className="h-3 w-3" />
                                  Inactive
                                </span>
                              )}
                            </td>
                            <td className="px-6 py-4">
                              <div className="flex items-center gap-2">
                                {u.emailVerified && (
                                  <Mail className="h-4 w-4 text-green-400"  />
                                )}
                                {u.phoneVerified && (
                                  <Phone className="h-4 w-4 text-green-400"  />
                                )}
                                {u.mfaEnabled && (
                                  <Lock className="h-4 w-4 text-cyan-400"  />
                                )}
                              </div>
                            </td>
                            <td className="px-6 py-4 text-sm text-slate-400">
                              {u.lastLogin
                                ? new Date(u.lastLogin).toLocaleDateString()
                                : "Never"}
                            </td>
                            <td className="px-6 py-4">
                              <div className="flex items-center gap-2">
                                <button
                                  onClick={() => {
                                    setEditingUser(u);
                                    setShowEditModal(true);
                                  }}
                                  disabled={processing === u.id}
                                  className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                  title="Edit user"
                                >
                                  <Edit className="h-3 w-3" />
                                  Edit
                                </button>
                                <button
                                  onClick={() => handleToggleActive(u.id, u.isActive)}
                                  disabled={processing === u.id}
                                  className={`flex items-center gap-1 px-3 py-1.5 text-white text-xs rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                                    u.isActive
                                      ? "bg-yellow-600 hover:bg-yellow-700"
                                      : "bg-green-600 hover:bg-green-700"
                                  }`}
                                  title={u.isActive ? "Deactivate user" : "Activate user"}
                                >
                                  {u.isActive ? (
                                    <>
                                      <UserX className="h-3 w-3" />
                                      Deactivate
                                    </>
                                  ) : (
                                    <>
                                      <UserCheck className="h-3 w-3" />
                                      Activate
                                    </>
                                  )}
                                </button>
                                <button
                                  onClick={() => handleDeleteUser(u.id, u.email)}
                                  disabled={processing === u.id || u.id === user.id}
                                  className="flex items-center gap-1 px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white text-xs rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                  title={u.id === user.id ? "Cannot delete yourself" : "Delete user"}
                                >
                                  <Trash2 className="h-3 w-3" />
                                  Delete
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Add User Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 rounded-xl border border-slate-700 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-slate-700">
              <h2 className="text-xl font-bold text-white">Add New User</h2>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                  <label className="block text-sm font-medium text-slate-300 mb-2">Full Name *</label>
                  <input
                    type="text"
                    value={newUser.fullName}
                    onChange={(e) => setNewUser({ ...newUser, fullName: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                    placeholder="John Doe"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Email *</label>
                  <input
                    type="email"
                    value={newUser.email}
                    onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                    placeholder="john@example.com"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Username *</label>
                  <input
                    type="text"
                    value={newUser.username}
                    onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                    placeholder="johndoe"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Password *</label>
                  <input
                    type="password"
                    value={newUser.password}
                    onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                    placeholder="••••••••"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Phone Number</label>
                  <input
                    type="tel"
                    value={newUser.phoneNumber}
                    onChange={(e) => setNewUser({ ...newUser, phoneNumber: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                    placeholder="+1 (555) 123-4567"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Role</label>
                  <select
                    value={newUser.role}
                    onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
                  >
                    <option value="VIEWER">Viewer</option>
                    <option value="TRADER">Trader</option>
                    <option value="ADMIN">Admin</option>
                    <option value="SUPER_ADMIN">Super Admin</option>
                    <option value="API_USER">API User</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Account Status</label>
                  <select
                    value={newUser.accountStatus}
                    onChange={(e) => setNewUser({ ...newUser, accountStatus: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
                  >
                    <option value="ACTIVE">Active</option>
                    <option value="INACTIVE">Inactive</option>
                    <option value="PENDING_APPROVAL">Pending Approval</option>
                    <option value="SUSPENDED">Suspended</option>
                    <option value="LOCKED">Locked</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">KYC Status</label>
                  <select
                    value={newUser.kycStatus}
                    onChange={(e) => setNewUser({ ...newUser, kycStatus: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
                  >
                    <option value="NOT_STARTED">Not Started</option>
                    <option value="IN_PROGRESS">In Progress</option>
                    <option value="PENDING_REVIEW">Pending Review</option>
                    <option value="APPROVED">Approved</option>
                    <option value="REJECTED">Rejected</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Risk Tolerance</label>
                  <select
                    value={newUser.riskTolerance}
                    onChange={(e) => setNewUser({ ...newUser, riskTolerance: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
                  >
                    <option value="CONSERVATIVE">Conservative</option>
                    <option value="MODERATE">Moderate</option>
                    <option value="AGGRESSIVE">Aggressive</option>
                    <option value="CUSTOM">Custom</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Subscription Tier</label>
                  <input
                    type="text"
                    value={newUser.subscriptionTier}
                    onChange={(e) => setNewUser({ ...newUser, subscriptionTier: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                    placeholder="FREE, BASIC, PRO, ENTERPRISE"
                  />
                </div>
                <div className="col-span-2">
                  <label className="flex items-center gap-2 text-sm text-slate-300">
                    <input
                      type="checkbox"
                      checked={newUser.canPlaceOrders}
                      onChange={(e) => setNewUser({ ...newUser, canPlaceOrders: e.target.checked })}
                      className="w-4 h-4 text-cyan-600 bg-slate-900 border-slate-700 rounded focus:ring-cyan-500"
                    />
                    Can Place Orders
                  </label>
                </div>
              </div>
            </div>
            <div className="p-6 border-t border-slate-700 flex justify-end gap-3">
              <button
                onClick={() => {
                  setShowAddModal(false);
                  setNewUser({
                    email: "",
                    username: "",
                    fullName: "",
                    phoneNumber: "",
                    timeZone: "America/New_York",
                    role: "VIEWER",
                    accountStatus: "ACTIVE",
                    kycStatus: "NOT_STARTED",
                    riskTolerance: "MODERATE",
                    canPlaceOrders: false,
                    subscriptionTier: "FREE",
                    password: ""
                  });
                }}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleAddUser}
                disabled={processing === "add"}
                className="flex items-center gap-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {processing === "add" ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Creating...
                  </>
                ) : (
                  <>
                    <UserPlus className="h-4 w-4" />
                    Create User
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit User Modal */}
      {showEditModal && editingUser && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 rounded-xl border border-slate-700 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-slate-700">
              <h2 className="text-xl font-bold text-white">Edit User</h2>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                  <label className="block text-sm font-medium text-slate-300 mb-2">Full Name *</label>
                  <input
                    type="text"
                    value={editingUser.fullName || ""}
                    onChange={(e) => setEditingUser({ ...editingUser, fullName: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Email</label>
                  <input
                    type="email"
                    value={editingUser.email}
                    onChange={(e) => setEditingUser({ ...editingUser, email: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Username *</label>
                  <input
                    type="text"
                    value={editingUser.username}
                    onChange={(e) => setEditingUser({ ...editingUser, username: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Phone Number</label>
                  <input
                    type="tel"
                    value={editingUser.phoneNumber || ""}
                    onChange={(e) => setEditingUser({ ...editingUser, phoneNumber: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Role</label>
                  <select
                    value={editingUser.role}
                    onChange={(e) => setEditingUser({ ...editingUser, role: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
                  >
                    <option value="VIEWER">Viewer</option>
                    <option value="TRADER">Trader</option>
                    <option value="ADMIN">Admin</option>
                    <option value="SUPER_ADMIN">Super Admin</option>
                    <option value="API_USER">API User</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Account Status</label>
                  <select
                    value={editingUser.accountStatus}
                    onChange={(e) => setEditingUser({ ...editingUser, accountStatus: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
                  >
                    <option value="ACTIVE">Active</option>
                    <option value="INACTIVE">Inactive</option>
                    <option value="PENDING_APPROVAL">Pending Approval</option>
                    <option value="SUSPENDED">Suspended</option>
                    <option value="LOCKED">Locked</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">KYC Status</label>
                  <select
                    value={editingUser.kycStatus}
                    onChange={(e) => setEditingUser({ ...editingUser, kycStatus: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
                  >
                    <option value="NOT_STARTED">Not Started</option>
                    <option value="IN_PROGRESS">In Progress</option>
                    <option value="PENDING_REVIEW">Pending Review</option>
                    <option value="APPROVED">Approved</option>
                    <option value="REJECTED">Rejected</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Risk Tolerance</label>
                  <select
                    value={editingUser.riskTolerance || "MODERATE"}
                    onChange={(e) => setEditingUser({ ...editingUser, riskTolerance: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
                  >
                    <option value="CONSERVATIVE">Conservative</option>
                    <option value="MODERATE">Moderate</option>
                    <option value="AGGRESSIVE">Aggressive</option>
                    <option value="CUSTOM">Custom</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Subscription Tier</label>
                  <input
                    type="text"
                    value={editingUser.subscriptionTier || ""}
                    onChange={(e) => setEditingUser({ ...editingUser, subscriptionTier: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                  />
                </div>
                <div className="col-span-2 space-y-2">
                  <label className="flex items-center gap-2 text-sm text-slate-300">
                    <input
                      type="checkbox"
                      checked={editingUser.canPlaceOrders}
                      onChange={(e) => setEditingUser({ ...editingUser, canPlaceOrders: e.target.checked })}
                      className="w-4 h-4 text-cyan-600 bg-slate-900 border-slate-700 rounded focus:ring-cyan-500"
                    />
                    Can Place Orders
                  </label>
                  <label className="flex items-center gap-2 text-sm text-slate-300">
                    <input
                      type="checkbox"
                      checked={editingUser.emailVerified}
                      onChange={(e) => setEditingUser({ ...editingUser, emailVerified: e.target.checked })}
                      className="w-4 h-4 text-cyan-600 bg-slate-900 border-slate-700 rounded focus:ring-cyan-500"
                    />
                    Email Verified
                  </label>
                  <label className="flex items-center gap-2 text-sm text-slate-300">
                    <input
                      type="checkbox"
                      checked={editingUser.phoneVerified}
                      onChange={(e) => setEditingUser({ ...editingUser, phoneVerified: e.target.checked })}
                      className="w-4 h-4 text-cyan-600 bg-slate-900 border-slate-700 rounded focus:ring-cyan-500"
                    />
                    Phone Verified
                  </label>
                  <label className="flex items-center gap-2 text-sm text-slate-300">
                    <input
                      type="checkbox"
                      checked={editingUser.mfaEnabled}
                      onChange={(e) => setEditingUser({ ...editingUser, mfaEnabled: e.target.checked })}
                      className="w-4 h-4 text-cyan-600 bg-slate-900 border-slate-700 rounded focus:ring-cyan-500"
                    />
                    MFA Enabled
                  </label>
                </div>
              </div>
            </div>
            <div className="p-6 border-t border-slate-700 flex justify-end gap-3">
              <button
                onClick={() => {
                  setShowEditModal(false);
                  setEditingUser(null);
                }}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleEditUser}
                disabled={processing === editingUser.id}
                className="flex items-center gap-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {processing === editingUser.id ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Edit className="h-4 w-4" />
                    Save Changes
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
