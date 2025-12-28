'use client';

import { ProtectedRoute } from '@/components/protected-route';
import { LayoutWrapper } from '@/components/layout-wrapper';
import { useAuth } from '@/lib/auth-context';
import { useState, useEffect } from 'react';
import { Users, UserPlus, Edit, Trash2, Shield, User } from 'lucide-react';
import Link from 'next/link';

interface UserData {
  id: string;
  email: string;
  username: string;
  fullName: string;
  role: 'ADMIN' | 'VIEWER';
  isActive: boolean;
  emailVerified: boolean;
  requiresApproval: boolean;
  approvedBy?: string;
  approvedAt?: string;
  createdAt: string;
  lastLogin?: string;
}

export default function UsersPage() {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<UserData[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingUser, setEditingUser] = useState<UserData | null>(null);
  const [newUser, setNewUser] = useState<{ email: string; username: string; fullName: string; role: 'ADMIN' | 'VIEWER'; password: string }>({ 
    email: '', 
    username: '',
    fullName: '', 
    role: 'VIEWER', 
    password: '' 
  });
  const [usernameError, setUsernameError] = useState('');
  const [emailError, setEmailError] = useState('');
  const [usernameSuggestions, setUsernameSuggestions] = useState<string[]>([]);
  const [checkingUsername, setCheckingUsername] = useState(false);

  useEffect(() => {
    if (currentUser?.role !== 'ADMIN') {
      window.location.href = '/dashboard';
      return;
    }
    fetchUsers();
  }, [currentUser]);

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
        setNewUser({ email: '', username: '', fullName: '', role: 'VIEWER', password: '' });
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

  const handleApproveUser = async (userId: string) => {
    if (!confirm('Approve this user account? They will be able to log in.')) return;

    try {
      const response = await fetch(`/api/users/${userId}/approve`, {
        method: 'POST',
      });

      if (response.ok) {
        fetchUsers();
      }
    } catch (error) {
      console.error('Error approving user:', error);
    }
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
                    Email
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Full Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Role
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Verification
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {users.map((user) => (
                  <tr key={user.id} className="hover:bg-gray-50">
                    {/* Email Column */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="flex-shrink-0 h-10 w-10 bg-gray-200 rounded-full flex items-center justify-center">
                          <User className="h-5 w-5 text-gray-600" />
                        </div>
                        <div className="ml-4">
                          <div className="text-sm text-gray-900">{user.email}</div>
                          <div className="text-xs text-gray-500">{user.username}</div>
                        </div>
                      </div>
                    </td>
                    {/* Full Name Column */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{user.fullName}</div>
                    </td>
                    {/* Role Column */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        user.role === 'ADMIN' 
                          ? 'bg-purple-100 text-purple-800' 
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {user.role === 'ADMIN' && <Shield className="h-3 w-3 mr-1" />}
                        {user.role}
                      </span>
                    </td>
                    {/* Verification Column */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full w-fit ${
                        user.emailVerified ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                      }`}>
                        {user.emailVerified ? '✓ Verified' : '⏳ Pending'}
                      </span>
                    </td>
                    {/* Status Column */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      {user.requiresApproval ? (
                        <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-orange-100 text-orange-800 w-fit">
                          🔒 Needs Approval
                        </span>
                      ) : (
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full w-fit ${
                          user.isActive ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {user.isActive ? '✓ Active' : '❌ Inactive'}
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(user.createdAt)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex justify-end gap-2">
                        {user.requiresApproval && (
                          <button
                            onClick={() => handleApproveUser(user.id)}
                            className="text-green-600 hover:text-green-900"
                            title="Approve user"
                          >
                            <Shield className="h-5 w-5" />
                          </button>
                        )}
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
            <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
              <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Add New User</h3>
                <div className="space-y-4">
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
                      Role
                    </label>
                    <select
                      value={newUser.role}
                      onChange={(e) => setNewUser({ ...newUser, role: e.target.value as 'ADMIN' | 'VIEWER' })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="VIEWER">Viewer</option>
                      <option value="ADMIN">Admin</option>
                    </select>
                  </div>
                </div>
                <div className="mt-6 flex justify-end gap-3">
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
          )}

          {/* Edit User Modal */}
          {showEditModal && editingUser && (
            <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
              <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Edit User</h3>
                <div className="space-y-4">
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
                      Role
                    </label>
                    <select
                      value={editingUser.role}
                      onChange={(e) => setEditingUser({ ...editingUser, role: e.target.value as 'ADMIN' | 'VIEWER' })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                    >
                      <option value="VIEWER">Viewer</option>
                      <option value="ADMIN">Admin</option>
                    </select>
                  </div>
                </div>
                <div className="mt-6 flex justify-end gap-3">
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
          )}
        </div>
      </div>
      </LayoutWrapper>
    </ProtectedRoute>
  );
}
