'use client';

import { ProtectedRoute } from '@/components/protected-route';
import { LayoutWrapper } from '@/components/layout-wrapper';
import { useAuth } from '@/lib/auth-context';
import { useState, useEffect } from 'react';
import { Plus, Edit2, Trash2, Eye, EyeOff, Save, X } from 'lucide-react';

interface ReleaseNote {
  id: string;
  version: string;
  title: string;
  description: string;
  changes: Array<{
    type: 'added' | 'changed' | 'fixed' | 'removed' | 'security';
    items: string[];
  }>;
  releaseDate: string;
  type: 'major' | 'minor' | 'patch';
  isPublished: boolean;
  createdBy: string;
}

interface ReleaseFormData {
  version: string;
  title: string;
  description: string;
  type: 'major' | 'minor' | 'patch';
  releaseDate: string;
  changes: Array<{
    type: 'added' | 'changed' | 'fixed' | 'removed' | 'security';
    items: string[];
  }>;
}

export default function AdminReleaseNotesPage() {
  const { user } = useAuth();
  const [releases, setReleases] = useState<ReleaseNote[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState<ReleaseFormData>({
    version: '',
    title: '',
    description: '',
    type: 'minor',
    releaseDate: new Date().toISOString().split('T')[0],
    changes: [{ type: 'added', items: [''] }],
  });

  useEffect(() => {
    if (user?.role !== 'ADMIN') {
      window.location.href = '/dashboard';
      return;
    }
    loadReleases();
  }, [user]);

  const loadReleases = async () => {
    try {
      const response = await fetch('/api/admin/release-notes');
      const data = await response.json();
      if (data.success) {
        setReleases(data.data);
      }
    } catch (error) {
      console.error('Error loading release notes:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const url = editingId 
        ? `/api/admin/release-notes/${editingId}`
        : '/api/admin/release-notes';
      
      const method = editingId ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (data.success) {
        setShowForm(false);
        setEditingId(null);
        resetForm();
        loadReleases();
      } else {
        alert('Failed to save release note: ' + (data.error || 'Unknown error'));
      }
    } catch (error) {
      console.error('Error saving release note:', error);
      alert('Failed to save release note');
    }
  };

  const handleEdit = (release: ReleaseNote) => {
    setFormData({
      version: release.version,
      title: release.title,
      description: release.description,
      type: release.type,
      releaseDate: release.releaseDate.split('T')[0],
      changes: release.changes,
    });
    setEditingId(release.id);
    setShowForm(true);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this release note?')) return;

    try {
      const response = await fetch(`/api/admin/release-notes/${id}`, {
        method: 'DELETE',
      });

      const data = await response.json();

      if (data.success) {
        loadReleases();
      } else {
        alert('Failed to delete release note');
      }
    } catch (error) {
      console.error('Error deleting release note:', error);
      alert('Failed to delete release note');
    }
  };

  const handleTogglePublish = async (id: string, currentStatus: boolean) => {
    try {
      const response = await fetch(`/api/admin/release-notes/${id}/publish`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ isPublished: !currentStatus }),
      });

      const data = await response.json();

      if (data.success) {
        loadReleases();
      } else {
        alert('Failed to update publish status');
      }
    } catch (error) {
      console.error('Error updating publish status:', error);
      alert('Failed to update publish status');
    }
  };

  const resetForm = () => {
    setFormData({
      version: '',
      title: '',
      description: '',
      type: 'minor',
      releaseDate: new Date().toISOString().split('T')[0],
      changes: [{ type: 'added', items: [''] }],
    });
  };

  const addChangeSection = () => {
    setFormData({
      ...formData,
      changes: [...formData.changes, { type: 'added', items: [''] }],
    });
  };

  const removeChangeSection = (index: number) => {
    const newChanges = formData.changes.filter((_, i) => i !== index);
    setFormData({ ...formData, changes: newChanges });
  };

  const updateChangeType = (index: number, type: string) => {
    const newChanges = [...formData.changes];
    newChanges[index].type = type as any;
    setFormData({ ...formData, changes: newChanges });
  };

  const addChangeItem = (sectionIndex: number) => {
    const newChanges = [...formData.changes];
    newChanges[sectionIndex].items.push('');
    setFormData({ ...formData, changes: newChanges });
  };

  const updateChangeItem = (sectionIndex: number, itemIndex: number, value: string) => {
    const newChanges = [...formData.changes];
    newChanges[sectionIndex].items[itemIndex] = value;
    setFormData({ ...formData, changes: newChanges });
  };

  const removeChangeItem = (sectionIndex: number, itemIndex: number) => {
    const newChanges = [...formData.changes];
    newChanges[sectionIndex].items = newChanges[sectionIndex].items.filter((_, i) => i !== itemIndex);
    setFormData({ ...formData, changes: newChanges });
  };

  if (user?.role !== 'ADMIN') {
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
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* Header */}
            <div className="flex justify-between items-center mb-8">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Manage Release Notes</h1>
                <p className="text-gray-600 mt-1">Create and publish release notes for users</p>
              </div>
              <button
                onClick={() => {
                  resetForm();
                  setEditingId(null);
                  setShowForm(true);
                }}
                className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                <Plus className="h-4 w-4 mr-2" />
                New Release
              </button>
            </div>

            {/* Form Modal */}
            {showForm && (
              <div className="fixed inset-0 bg-gray-600 bg-opacity-75 z-50 flex items-center justify-center p-4">
                <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
                  <div className="p-6">
                    <div className="flex justify-between items-center mb-6">
                      <h2 className="text-2xl font-bold text-gray-900">
                        {editingId ? 'Edit Release Note' : 'New Release Note'}
                      </h2>
                      <button
                        onClick={() => {
                          setShowForm(false);
                          setEditingId(null);
                          resetForm();
                        }}
                        className="text-gray-400 hover:text-gray-600"
                      >
                        <X className="h-6 w-6" />
                      </button>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-6">
                      {/* Basic Info */}
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Version *
                          </label>
                          <input
                            type="text"
                            required
                            placeholder="1.0.0"
                            value={formData.version}
                            onChange={(e) => setFormData({ ...formData, version: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Type *
                          </label>
                          <select
                            value={formData.type}
                            onChange={(e) => setFormData({ ...formData, type: e.target.value as any })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                          >
                            <option value="major">Major</option>
                            <option value="minor">Minor</option>
                            <option value="patch">Patch</option>
                          </select>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Release Date *
                          </label>
                          <input
                            type="date"
                            required
                            value={formData.releaseDate}
                            onChange={(e) => setFormData({ ...formData, releaseDate: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />
                        </div>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Title *
                        </label>
                        <input
                          type="text"
                          required
                          placeholder="Admin Platform Launch"
                          value={formData.title}
                          onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Description *
                        </label>
                        <textarea
                          required
                          rows={3}
                          placeholder="Brief summary of this release..."
                          value={formData.description}
                          onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>

                      {/* Changes */}
                      <div>
                        <div className="flex justify-between items-center mb-4">
                          <label className="block text-sm font-medium text-gray-700">
                            Changes *
                          </label>
                          <button
                            type="button"
                            onClick={addChangeSection}
                            className="text-sm text-blue-600 hover:text-blue-700"
                          >
                            + Add Section
                          </button>
                        </div>

                        <div className="space-y-4">
                          {formData.changes.map((change, sectionIdx) => (
                            <div key={sectionIdx} className="border border-gray-200 rounded-lg p-4">
                              <div className="flex justify-between items-center mb-3">
                                <select
                                  value={change.type}
                                  onChange={(e) => updateChangeType(sectionIdx, e.target.value)}
                                  className="px-3 py-1 border border-gray-300 rounded-lg text-sm"
                                >
                                  <option value="added">✨ Added</option>
                                  <option value="changed">🔄 Changed</option>
                                  <option value="fixed">🐛 Fixed</option>
                                  <option value="removed">🗑️ Removed</option>
                                  <option value="security">🔒 Security</option>
                                </select>
                                {formData.changes.length > 1 && (
                                  <button
                                    type="button"
                                    onClick={() => removeChangeSection(sectionIdx)}
                                    className="text-red-600 hover:text-red-700"
                                  >
                                    <Trash2 className="h-4 w-4" />
                                  </button>
                                )}
                              </div>

                              <div className="space-y-2">
                                {change.items.map((item, itemIdx) => (
                                  <div key={itemIdx} className="flex gap-2">
                                    <input
                                      type="text"
                                      placeholder="Change description..."
                                      value={item}
                                      onChange={(e) => updateChangeItem(sectionIdx, itemIdx, e.target.value)}
                                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                    {change.items.length > 1 && (
                                      <button
                                        type="button"
                                        onClick={() => removeChangeItem(sectionIdx, itemIdx)}
                                        className="text-red-600 hover:text-red-700"
                                      >
                                        <X className="h-4 w-4" />
                                      </button>
                                    )}
                                  </div>
                                ))}
                                <button
                                  type="button"
                                  onClick={() => addChangeItem(sectionIdx)}
                                  className="text-sm text-blue-600 hover:text-blue-700"
                                >
                                  + Add Item
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex justify-end gap-3 pt-4 border-t">
                        <button
                          type="button"
                          onClick={() => {
                            setShowForm(false);
                            setEditingId(null);
                            resetForm();
                          }}
                          className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
                        >
                          Cancel
                        </button>
                        <button
                          type="submit"
                          className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                        >
                          <Save className="h-4 w-4 mr-2" />
                          {editingId ? 'Update' : 'Create'} Release
                        </button>
                      </div>
                    </form>
                  </div>
                </div>
              </div>
            )}

            {/* Release Notes List */}
            <div className="space-y-4">
              {releases.length === 0 ? (
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No Release Notes Yet</h3>
                  <p className="text-gray-600 mb-4">Create your first release note to get started.</p>
                  <button
                    onClick={() => setShowForm(true)}
                    className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Create Release Note
                  </button>
                </div>
              ) : (
                releases.map((release) => (
                  <div key={release.id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-xl font-bold text-gray-900">v{release.version}</h3>
                          <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                            release.type === 'major' ? 'bg-red-100 text-red-800' :
                            release.type === 'minor' ? 'bg-blue-100 text-blue-800' :
                            'bg-green-100 text-green-800'
                          }`}>
                            {release.type.toUpperCase()}
                          </span>
                          <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                            release.isPublished ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                          }`}>
                            {release.isPublished ? 'Published' : 'Draft'}
                          </span>
                        </div>
                        <h4 className="text-lg font-semibold text-gray-800 mb-1">{release.title}</h4>
                        <p className="text-gray-600 text-sm mb-2">{release.description}</p>
                        <p className="text-xs text-gray-500">
                          {new Date(release.releaseDate).toLocaleDateString()}
                        </p>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleTogglePublish(release.id, release.isPublished)}
                          className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg"
                          title={release.isPublished ? 'Unpublish' : 'Publish'}
                        >
                          {release.isPublished ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                        </button>
                        <button
                          onClick={() => handleEdit(release)}
                          className="p-2 text-blue-600 hover:text-blue-900 hover:bg-blue-50 rounded-lg"
                          title="Edit"
                        >
                          <Edit2 className="h-5 w-5" />
                        </button>
                        <button
                          onClick={() => handleDelete(release.id)}
                          className="p-2 text-red-600 hover:text-red-900 hover:bg-red-50 rounded-lg"
                          title="Delete"
                        >
                          <Trash2 className="h-5 w-5" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </LayoutWrapper>
    </ProtectedRoute>
  );
}
