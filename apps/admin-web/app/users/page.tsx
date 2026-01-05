'use client';

import { ProtectedRoute } from '@/components/protected-route';
import { LayoutWrapper } from '@/components/layout-wrapper';
import { useAuth } from '@/lib/auth-context';
import { useState, useEffect } from 'react';
import { Users, UserPlus, Edit, Trash2, Shield, User, Phone, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import Link from 'next/link';

interface UserData {
  id: string;
  email: string;
  username: string;
  fullName: string;
  phoneNumber?: string;
  timeZone?: string;
  role: 'SUPER_ADMIN' | 'ADMIN' | 'TRADER' | 'VIEWER' | 'API_USER';
  isActive: boolean;
  accountStatus: 'ACTIVE' | 'INACTIVE' | 'PENDING_APPROVAL' | 'SUSPENDED' | 'LOCKED' | 'ARCHIVED';
  emailVerified: boolean;
  phoneVerified: boolean;
  mfaEnabled: boolean;
  requiresApproval: boolean;
  approvedBy?: string;
  approvedAt?: string;
  kycStatus: 'NOT_STARTED' | 'IN_PROGRESS' | 'PENDING_REVIEW' | 'APPROVED' | 'REJECTED' | 'EXPIRED';
  alpacaAccountId?: string;
  riskTolerance?: 'CONSERVATIVE' | 'MODERATE' | 'AGGRESSIVE' | 'CUSTOM';
  canPlaceOrders: boolean;
  subscriptionTier?: string;
  createdAt: string;
  lastLogin?: string;
  lastLoginIp?: string;
}

export default function UsersPage() {
  const { user: currentUser, loading: authLoading } = useAuth();
  const [users, setUsers] = useState<UserData[]>([]);
  const [filteredUsers, setFilteredUsers] = useState<UserData[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingUser, setEditingUser] = useState<UserData | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [newUser, setNewUser] = useState<{ 
    email: string; 
    username: string; 
    fullName: string; 
    phoneNumber?: string;
    timeZone?: string;
    role: 'SUPER_ADMIN' | 'ADMIN' | 'TRADER' | 'VIEWER' | 'API_USER'; 
    accountStatus: 'ACTIVE' | 'INACTIVE' | 'PENDING_APPROVAL' | 'SUSPENDED' | 'LOCKED' | 'ARCHIVED';
    kycStatus: 'NOT_STARTED' | 'IN_PROGRESS' | 'PENDING_REVIEW' | 'APPROVED' | 'REJECTED' | 'EXPIRED';
    riskTolerance?: 'CONSERVATIVE' | 'MODERATE' | 'AGGRESSIVE' | 'CUSTOM';
    canPlaceOrders: boolean;
    subscriptionTier?: string;
    password: string;
  }>({ 
    email: '', 
    username: '',
    fullName: '', 
    phoneNumber: '',
    timeZone: 'America/New_York',
    role: 'VIEWER', 
    accountStatus: 'ACTIVE',
    kycStatus: 'NOT_STARTED',
    riskTolerance: 'MODERATE',
    canPlaceOrders: false,
    subscriptionTier: 'FREE',
    password: '' 
  });
  const [usernameError, setUsernameError] = useState('');
  const [emailError, setEmailError] = useState('');
  const [usernameSuggestions, setUsernameSuggestions] = useState<string[]>([]);
  const [checkingUsername, setCheckingUsername] = useState(false);

  useEffect(() => {
    // Wait for auth to finish loading before checking role
    if (authLoading) {
      return;
    }
    
    if (currentUser?.role !== 'ADMIN') {
      window.location.href = '/dashboard';
      return;
    }
    fetchUsers();
  }, [currentUser, authLoading]);

  useEffect(() => {
    // Apply filters and search
    let filtered = users;

    // Search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(user => 
        user.email.toLowerCase().includes(term) ||
        user.username.toLowerCase().includes(term) ||
        user.fullName.toLowerCase().includes(term)
      );
    }

    // Role filter
    if (roleFilter !== 'all') {
      filtered = filtered.filter(user => user.role === roleFilter);
    }

    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(user => user.accountStatus === statusFilter);
    }

    setFilteredUsers(filtered);
  }, [users, searchTerm, roleFilter, statusFilter]);

  const fetchUsers = async () => {
    try {
      const response = await fetch('/api/users');
      if (response.ok) {
        const data = await response.json();
        setUsers(data.users || []);
      }
    } catch (error) {
      console.error('Error fetching users:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddUser = async () => {
    try {
      const response = await fetch('/api/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newUser),
      });

      if (response.ok) {
        setShowAddModal(false);
        setNewUser({ 
          email: '', 
          username: '', 
          fullName: '', 
          phoneNumber: '',
          timeZone: 'America/New_York',
          role: 'VIEWER', 
          accountStatus: 'ACTIVE',
          kycStatus: 'NOT_STARTED',
          riskTolerance: 'MODERATE',
          canPlaceOrders: false,
          subscriptionTier: 'FREE',
          password: '' 
        });
        fetchUsers();
      }
    } catch (error) {
      console.error('Error adding user:', error);
    }
  };

  const checkUsernameAvailability = async (username: string, email: string, excludeUserId?: string) => {
    if (!username && !email) return;
    
    setCheckingUsername(true);
    try {
      const response = await fetch('/api/users/check-username', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, excludeUserId }),
      });

      if (response.ok) {
        const data = await response.json();
        
        if (username && !data.usernameAvailable) {
          setUsernameError('Username is already taken');
          setUsernameSuggestions(data.suggestions || []);
        } else {
          setUsernameError('');
          setUsernameSuggestions([]);
        }

        if (email && !data.emailAvailable) {
          setEmailError('Email is already registered');
        } else {
          setEmailError('');
        }
      }
    } catch (error) {
      console.error('Error checking username:', error);
    } finally {
      setCheckingUsername(false);
    }
  };

  const handleEditUser = async () => {
    if (!editingUser) return;
    
    // Check username availability before saving
    await checkUsernameAvailability(editingUser.username, '', editingUser.id);
    
    if (usernameError) {
      return; // Don't save if username is taken
    }

    try {
      const response = await fetch(`/api/users/${editingUser.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          fullName: editingUser.fullName,
          username: editingUser.username,
          role: editingUser.role,
          emailVerified: editingUser.emailVerified,
          requiresApproval: editingUser.requiresApproval,
        }),
      });

      if (response.ok) {
        setShowEditModal(false);
        setEditingUser(null);
        setUsernameError('');
        setUsernameSuggestions([]);
        fetchUsers();
      }
    } catch (error) {
      console.error('Error editing user:', error);
    }
  };

  const handleToggleActive = async (userId: string, isActive: boolean) => {
    try {
      const response = await fetch(`/api/users/${userId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ isActive: !isActive }),
      });

      if (response.ok) {
        fetchUsers();
      }
    } catch (error) {
      console.error('Error updating user:', error);
    }
  };

  const handleDeleteUser = async (userId: string) => {
    if (!confirm('Are you sure you want to delete this user?')) return;

    try {
      const response = await fetch(`/api/users/${userId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        fetchUsers();
      }
    } catch (error) {
      console.error('Error deleting user:', error);
    }
  };

  const getStatusBadge = (status: string) => {
    const badges: Record<string, string> = {
      ACTIVE: 'bg-green-100 text-green-800',
      INACTIVE: 'bg-gray-100 text-gray-800',
      PENDING_APPROVAL: 'bg-yellow-100 text-yellow-800',
      SUSPENDED: 'bg-red-100 text-red-800',
      LOCKED: 'bg-red-100 text-red-800',
      ARCHIVED: 'bg-gray-100 text-gray-800',
    };
    return badges[status] || 'bg-gray-100 text-gray-800';
  };

  const getKycBadge = (status: string) => {
    const badges: Record<string, string> = {
      NOT_STARTED: 'bg-gray-100 text-gray-800',
      IN_PROGRESS: 'bg-blue-100 text-blue-800',
      PENDING_REVIEW: 'bg-yellow-100 text-yellow-800',
      APPROVED: 'bg-green-100 text-green-800',
      REJECTED: 'bg-red-100 text-red-800',
      EXPIRED: 'bg-orange-100 text-orange-800',
    };
    return badges[status] || 'bg-gray-100 text-gray-800';
  };


  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  if (currentUser?.role !== 'ADMIN') {
    return null;
  }

  if (loading) {
    return (
      <ProtectedRoute>
        <LayoutWrapper>
        <div className="min-h-screen flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
        </LayoutWrapper>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute>
      <LayoutWrapper>
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Header */}
          <div className="mb-6">
            <div className="flex justify-between items-center mb-4">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">User Management</h1>
                <p className="mt-1 text-gray-600">
                  {users.length} user{users.length !== 1 ? 's' : ''} with platform access
                </p>
              </div>
              <div className="flex items-center gap-4">
                <button
                  onClick={() => setShowAddModal(true)}
                  className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  <UserPlus className="h-4 w-4 mr-2" />
                  Add User
                </button>
                <Link
                  href="/dashboard"
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  ← Back to Dashboard
                </Link>
              </div>
            </div>
          </div>

          {/* Users Table */}
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    User
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Role
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Account Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    KYC Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Security
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Last Login
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {users.map((user) => (
                  <tr key={user.id} className="hover:bg-gray-50">
                    {/* User Column - Combined */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="flex-shrink-0 h-10 w-10 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-full flex items-center justify-center">
                          <User className="h-5 w-5 text-white" />
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900">{user.fullName}</div>
                          <div className="text-xs text-gray-500">{user.email}</div>
                          {user.phoneNumber && (
                            <div className="text-xs text-gray-400 flex items-center gap-1 mt-0.5">
                              <Phone className="h-3 w-3" />
                              {user.phoneNumber}
                            </div>
                          )}
                        </div>
                      </div>
                    </td>
                    {/* Role Column */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        user.role === 'SUPER_ADMIN' ? 'bg-red-100 text-red-800' :
                        user.role === 'ADMIN' ? 'bg-purple-100 text-purple-800' :
                        user.role === 'TRADER' ? 'bg-blue-100 text-blue-800' :
                        user.role === 'API_USER' ? 'bg-gray-100 text-gray-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                        {(user.role === 'ADMIN' || user.role === 'SUPER_ADMIN') && <Shield className="h-3 w-3 mr-1" />}
                        {user.role}
                      </span>
                    </td>
                    {/* Account Status Column */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2.5 py-0.5 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusBadge(user.accountStatus)}`}>
                        {user.accountStatus.replace('_', ' ')}
                      </span>
                    </td>
                    {/* KYC Status Column */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2.5 py-0.5 inline-flex text-xs leading-5 font-semibold rounded-full ${getKycBadge(user.kycStatus)}`}>
                        {user.kycStatus.replace('_', ' ')}
                      </span>
                    </td>
                    {/* Security Column - Icons */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        {user.emailVerified && (
                          <div title="Email Verified">
                            <CheckCircle className="h-4 w-4 text-green-500" />
                          </div>
                        )}
                        {user.mfaEnabled && (
                          <div title="MFA Enabled">
                            <Shield className="h-4 w-4 text-blue-500" />
                          </div>
                        )}
                        {user.phoneVerified && (
                          <div title="Phone Verified">
                            <Phone className="h-4 w-4 text-purple-500" />
                          </div>
                        )}
                        {!user.emailVerified && !user.mfaEnabled && !user.phoneVerified && (
                          <span className="text-xs text-gray-400">None</span>
                        )}
                      </div>
                    </td>
                    {/* Last Login Column */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {user.lastLogin ? formatDate(user.lastLogin) : 'Never'}
                      </div>
                      {user.lastLoginIp && (
                        <div className="text-xs text-gray-500">{user.lastLoginIp}</div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex justify-end gap-2">
                        <button
                          onClick={() => {
                            setEditingUser(user);
                            setShowEditModal(true);
                          }}
                          className="text-blue-600 hover:text-blue-900"
                          title="Edit user"
                        >
                          <Edit className="h-5 w-5" />
                        </button>
                        <button
                          onClick={() => handleDeleteUser(user.id)}
                          disabled={user.id === currentUser?.id}
                          className="text-red-600 hover:text-red-900 disabled:opacity-50 disabled:cursor-not-allowed"
                          title={user.id === currentUser?.id ? 'Cannot delete your own account' : 'Delete user'}
                        >
                          <Trash2 className="h-5 w-5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Add User Modal */}
          {showAddModal && (
            <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50 p-4">
              <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col">
                <div className="p-6 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900">Add New User</h3>
                </div>
                <div className="p-6 overflow-y-auto flex-1">
                  <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Full Name
                    </label>
                    <input
                      type="text"
                      value={newUser.fullName}
                      onChange={(e) => setNewUser({ ...newUser, fullName: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="John Doe"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Email
                    </label>
                    <input
                      type="email"
                      value={newUser.email}
                      onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="john@example.com"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Password
                    </label>
                    <input
                      type="password"
                      value={newUser.password}
                      onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="••••••••"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Phone Number (Optional)
                    </label>
                    <input
                      type="tel"
                      value={newUser.phoneNumber}
                      onChange={(e) => setNewUser({ ...newUser, phoneNumber: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="+1 (555) 123-4567"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Time Zone
                    </label>
                    <select
                      value={newUser.timeZone}
                      onChange={(e) => setNewUser({ ...newUser, timeZone: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="America/New_York">Eastern Time</option>
                      <option value="America/Chicago">Central Time</option>
                      <option value="America/Denver">Mountain Time</option>
                      <option value="America/Los_Angeles">Pacific Time</option>
                      <option value="UTC">UTC</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Role
                    </label>
                    <select
                      value={newUser.role}
                      onChange={(e) => setNewUser({ ...newUser, role: e.target.value as any })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="VIEWER">Viewer</option>
                      <option value="TRADER">Trader</option>
                      <option value="ADMIN">Admin</option>
                      <option value="SUPER_ADMIN">Super Admin</option>
                      <option value="API_USER">API User</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Account Status
                    </label>
                    <select
                      value={newUser.accountStatus}
                      onChange={(e) => setNewUser({ ...newUser, accountStatus: e.target.value as any })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="ACTIVE">Active</option>
                      <option value="INACTIVE">Inactive</option>
                      <option value="PENDING_APPROVAL">Pending Approval</option>
                      <option value="SUSPENDED">Suspended</option>
                      <option value="LOCKED">Locked</option>
                      <option value="ARCHIVED">Archived</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      KYC Status
                    </label>
                    <select
                      value={newUser.kycStatus}
                      onChange={(e) => setNewUser({ ...newUser, kycStatus: e.target.value as any })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="NOT_STARTED">Not Started</option>
                      <option value="IN_PROGRESS">In Progress</option>
                      <option value="PENDING_REVIEW">Pending Review</option>
                      <option value="APPROVED">Approved</option>
                      <option value="REJECTED">Rejected</option>
                      <option value="EXPIRED">Expired</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Risk Tolerance
                    </label>
                    <select
                      value={newUser.riskTolerance}
                      onChange={(e) => setNewUser({ ...newUser, riskTolerance: e.target.value as any })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="CONSERVATIVE">Conservative</option>
                      <option value="MODERATE">Moderate</option>
                      <option value="AGGRESSIVE">Aggressive</option>
                      <option value="CUSTOM">Custom</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Subscription Tier
                    </label>
                    <input
                      type="text"
                      value={newUser.subscriptionTier}
                      onChange={(e) => setNewUser({ ...newUser, subscriptionTier: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="FREE, BASIC, PRO, ENTERPRISE"
                    />
                  </div>
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="canPlaceOrders"
                      checked={newUser.canPlaceOrders}
                      onChange={(e) => setNewUser({ ...newUser, canPlaceOrders: e.target.checked })}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label htmlFor="canPlaceOrders" className="ml-2 block text-sm text-gray-900">
                      Can Place Orders
                    </label>
                  </div>
                  </div>
                </div>
                <div className="p-6 border-t border-gray-200">
                  <div className="flex justify-end gap-3">
                    <button
                      onClick={() => setShowAddModal(false)}
                      className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleAddUser}
                      disabled={!newUser.email || !newUser.username || !newUser.fullName || !newUser.password}
                      className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Add User
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Edit User Modal */}
          {showEditModal && editingUser && (
            <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50 p-4">
              <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col">
                <div className="p-6 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900">Edit User</h3>
                </div>
                <div className="p-6 overflow-y-auto flex-1">
                  <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Full Name
                    </label>
                    <input
                      type="text"
                      value={editingUser.fullName}
                      onChange={(e) => setEditingUser({ ...editingUser, fullName: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Username
                    </label>
                    <input
                      type="text"
                      value={editingUser.username}
                      onChange={(e) => {
                        setEditingUser({ ...editingUser, username: e.target.value });
                        setUsernameError('');
                        setUsernameSuggestions([]);
                      }}
                      onBlur={() => checkUsernameAvailability(editingUser.username, '', editingUser.id)}
                      className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900 ${
                        usernameError ? 'border-red-500' : 'border-gray-300'
                      }`}
                    />
                    {checkingUsername && (
                      <p className="text-xs text-gray-500 mt-1">Checking availability...</p>
                    )}
                    {usernameError && (
                      <div className="mt-2">
                        <p className="text-xs text-red-600">{usernameError}</p>
                        {usernameSuggestions.length > 0 && (
                          <div className="mt-2">
                            <p className="text-xs text-gray-600 mb-1">Suggestions:</p>
                            <div className="flex flex-wrap gap-2">
                              {usernameSuggestions.map((suggestion) => (
                                <button
                                  key={suggestion}
                                  type="button"
                                  onClick={() => {
                                    setEditingUser({ ...editingUser, username: suggestion });
                                    setUsernameError('');
                                    setUsernameSuggestions([]);
                                  }}
                                  className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                                >
                                  {suggestion}
                                </button>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Email (read-only)
                    </label>
                    <input
                      type="email"
                      value={editingUser.email}
                      disabled
                      className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-100 text-gray-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Phone Number
                    </label>
                    <input
                      type="tel"
                      value={editingUser.phoneNumber || ''}
                      onChange={(e) => setEditingUser({ ...editingUser, phoneNumber: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                      placeholder="+1 (555) 123-4567"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Time Zone
                    </label>
                    <select
                      value={editingUser.timeZone || 'America/New_York'}
                      onChange={(e) => setEditingUser({ ...editingUser, timeZone: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                    >
                      <option value="America/New_York">Eastern Time</option>
                      <option value="America/Chicago">Central Time</option>
                      <option value="America/Denver">Mountain Time</option>
                      <option value="America/Los_Angeles">Pacific Time</option>
                      <option value="UTC">UTC</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Role
                    </label>
                    <select
                      value={editingUser.role}
                      onChange={(e) => setEditingUser({ ...editingUser, role: e.target.value as any })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                    >
                      <option value="VIEWER">Viewer</option>
                      <option value="TRADER">Trader</option>
                      <option value="ADMIN">Admin</option>
                      <option value="SUPER_ADMIN">Super Admin</option>
                      <option value="API_USER">API User</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Account Status
                    </label>
                    <select
                      value={editingUser.accountStatus}
                      onChange={(e) => setEditingUser({ ...editingUser, accountStatus: e.target.value as any })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                    >
                      <option value="ACTIVE">Active</option>
                      <option value="INACTIVE">Inactive</option>
                      <option value="PENDING_APPROVAL">Pending Approval</option>
                      <option value="SUSPENDED">Suspended</option>
                      <option value="LOCKED">Locked</option>
                      <option value="ARCHIVED">Archived</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      KYC Status
                    </label>
                    <select
                      value={editingUser.kycStatus}
                      onChange={(e) => setEditingUser({ ...editingUser, kycStatus: e.target.value as any })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                    >
                      <option value="NOT_STARTED">Not Started</option>
                      <option value="IN_PROGRESS">In Progress</option>
                      <option value="PENDING_REVIEW">Pending Review</option>
                      <option value="APPROVED">Approved</option>
                      <option value="REJECTED">Rejected</option>
                      <option value="EXPIRED">Expired</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Risk Tolerance
                    </label>
                    <select
                      value={editingUser.riskTolerance || 'MODERATE'}
                      onChange={(e) => setEditingUser({ ...editingUser, riskTolerance: e.target.value as any })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                    >
                      <option value="CONSERVATIVE">Conservative</option>
                      <option value="MODERATE">Moderate</option>
                      <option value="AGGRESSIVE">Aggressive</option>
                      <option value="CUSTOM">Custom</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Subscription Tier
                    </label>
                    <input
                      type="text"
                      value={editingUser.subscriptionTier || ''}
                      onChange={(e) => setEditingUser({ ...editingUser, subscriptionTier: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                      placeholder="FREE, BASIC, PRO, ENTERPRISE"
                    />
                  </div>
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="editCanPlaceOrders"
                      checked={editingUser.canPlaceOrders}
                      onChange={(e) => setEditingUser({ ...editingUser, canPlaceOrders: e.target.checked })}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label htmlFor="editCanPlaceOrders" className="ml-2 block text-sm text-gray-900">
                      Can Place Orders
                    </label>
                  </div>
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="editEmailVerified"
                      checked={editingUser.emailVerified}
                      onChange={(e) => setEditingUser({ ...editingUser, emailVerified: e.target.checked })}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label htmlFor="editEmailVerified" className="ml-2 block text-sm text-gray-900">
                      Email Verified
                    </label>
                  </div>
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="editPhoneVerified"
                      checked={editingUser.phoneVerified}
                      onChange={(e) => setEditingUser({ ...editingUser, phoneVerified: e.target.checked })}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label htmlFor="editPhoneVerified" className="ml-2 block text-sm text-gray-900">
                      Phone Verified
                    </label>
                  </div>
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="editMfaEnabled"
                      checked={editingUser.mfaEnabled}
                      onChange={(e) => setEditingUser({ ...editingUser, mfaEnabled: e.target.checked })}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label htmlFor="editMfaEnabled" className="ml-2 block text-sm text-gray-900">
                      MFA Enabled
                    </label>
                  </div>
                  <div className="col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Last Login
                    </label>
                    <input
                      type="text"
                      value={editingUser.lastLogin ? new Date(editingUser.lastLogin).toLocaleString() : "Never"}
                      disabled
                      className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-100 text-gray-500"
                    />
                  </div>
                  </div>
                </div>
                <div className="p-6 border-t border-gray-200">
                  <div className="flex justify-end gap-3">
                    <button
                      onClick={() => {
                        setShowEditModal(false);
                        setEditingUser(null);
                      }}
                      className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleEditUser}
                      disabled={!editingUser.fullName || !editingUser.username}
                      className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Save Changes
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
      </LayoutWrapper>
    </ProtectedRoute>
  );
}
