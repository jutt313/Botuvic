import React, { useState, useEffect } from 'react';
import { useAuthStore } from '@/store/authStore';
import { useNavigate } from 'react-router-dom';
import api from '@/services/api';
import { 
  User, 
  Settings, 
  LogOut, 
  Bot,
  X,
  Bell,
  CreditCard,
  AlertTriangle,
  Save,
  Upload,
  Trash2,
  Plus
} from 'lucide-react';

export const ProfilePopup = ({ isOpen, onClose }) => {
  const { user, logout, updateUser } = useAuthStore();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('profile');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Profile state
  const [profileName, setProfileName] = useState('');
  const [profileEmail, setProfileEmail] = useState('');
  const [avatarUrl, setAvatarUrl] = useState('');
  const [avatarFile, setAvatarFile] = useState(null);
  
  // LLM state
  const [llms, setLlms] = useState([]);
  const [showAddLLM, setShowAddLLM] = useState(false);
  const [newLLM, setNewLLM] = useState({ provider: '', model: '', api_key: '' });
  
  // Danger zone state
  const [confirmDeleteProjects, setConfirmDeleteProjects] = useState('');
  const [confirmDeleteAccount, setConfirmDeleteAccount] = useState('');

  useEffect(() => {
    if (isOpen && user) {
      setProfileName(user.name || '');
      setProfileEmail(user.email || '');
      setAvatarUrl(user.avatar_url || '');
      loadLLMs();
    }
  }, [isOpen, user]);

  const loadLLMs = async () => {
    try {
      const response = await api.get('/auth/llms');
      setLlms(response.data || []);
    } catch (err) {
      console.error('Failed to load LLMs:', err);
    }
  };

  const handleSaveProfile = async () => {
    setLoading(true);
    setError('');
    setSuccess('');
    
    try {
      // If avatar file selected, upload it first (placeholder - would need file upload endpoint)
      let finalAvatarUrl = avatarUrl;
      if (avatarFile) {
        // For now, use a placeholder URL
        // In production, upload to Supabase Storage and get URL
        finalAvatarUrl = URL.createObjectURL(avatarFile);
      }
      
      const response = await api.patch('/auth/profile', {
        name: profileName,
        avatar_url: finalAvatarUrl
      });
      
      updateUser(response.data);
      setSuccess('Profile updated successfully!');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  const handleAddLLM = async () => {
    if (!newLLM.provider || !newLLM.api_key) {
      setError('Provider and API key are required');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      await api.post('/auth/llms', newLLM);
      setNewLLM({ provider: '', model: '', api_key: '' });
      setShowAddLLM(false);
      await loadLLMs();
      setSuccess('LLM added successfully!');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to add LLM');
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveLLM = async (llmId) => {
    if (!confirm('Are you sure you want to remove this LLM?')) return;
    
    setLoading(true);
    try {
      await api.delete(`/auth/llms/${llmId}`);
      await loadLLMs();
      setSuccess('LLM removed successfully!');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to remove LLM');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAllProjects = async () => {
    if (confirmDeleteProjects !== 'DELETE') {
      setError('Please type DELETE to confirm');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      await api.delete('/auth/projects/all');
      setSuccess('All projects deleted successfully!');
      setConfirmDeleteProjects('');
      setTimeout(() => {
        setSuccess('');
        onClose();
        window.location.reload();
      }, 2000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete projects');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (confirmDeleteAccount !== 'DELETE MY ACCOUNT') {
      setError('Please type DELETE MY ACCOUNT to confirm');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      await api.delete('/auth/account');
      await logout();
      navigate('/login');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete account');
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const getInitials = (name, email) => {
    if (name) {
      return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
    }
    return email ? email[0].toUpperCase() : 'U';
  };

  if (!isOpen) return null;

  const tabs = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'billing', label: 'Billing', icon: CreditCard },
    { id: 'llm', label: 'LLM', icon: Bot },
    { id: 'danger', label: 'Danger Zone', icon: AlertTriangle },
  ];

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50"
        onClick={onClose}
      />

      {/* Popup */}
      <div className="fixed inset-0 flex items-center justify-center z-50 p-2 sm:p-4">
        <div className="w-full max-w-2xl max-h-[95vh] sm:max-h-[90vh] overflow-hidden rounded-xl sm:rounded-2xl glass border border-white/10 shadow-2xl flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between p-4 sm:p-6 border-b border-white/10">
            <h2 className="text-xl sm:text-2xl font-bold text-white">Profile Settings</h2>
            <button
              onClick={onClose}
              className="p-2 hover:bg-white/10 rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Tabs */}
          <div className="flex border-b border-white/10 overflow-x-auto">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-1 sm:gap-2 px-3 sm:px-6 py-3 sm:py-4 border-b-2 transition-colors text-xs sm:text-sm ${
                    activeTab === tab.id
                      ? 'border-primary text-primary'
                      : 'border-transparent text-text-muted hover:text-text'
                  }`}
                >
                  <Icon className="w-3 h-3 sm:w-4 sm:h-4" />
                  <span className="whitespace-nowrap">{tab.label}</span>
                </button>
              );
            })}
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-4 sm:p-6">
            {error && (
              <div className="mb-4 p-3 bg-error/20 border border-error/30 rounded-lg text-error text-sm">
                {error}
              </div>
            )}
            {success && (
              <div className="mb-4 p-3 bg-success/20 border border-success/30 rounded-lg text-success text-sm">
                {success}
              </div>
            )}

            {/* Profile Tab */}
            {activeTab === 'profile' && (
              <div className="space-y-6">
                {/* Avatar */}
                <div className="flex items-center gap-6">
                  <div className="relative">
                    {avatarUrl || avatarFile ? (
                      <img
                        src={avatarFile ? URL.createObjectURL(avatarFile) : avatarUrl}
                        alt="Avatar"
                        className="w-24 h-24 rounded-full object-cover border-2 border-primary/50"
                      />
                    ) : (
                      <div className="w-24 h-24 rounded-full bg-gradient-to-r from-primary to-secondary flex items-center justify-center text-white text-2xl font-bold">
                        {getInitials(profileName, profileEmail)}
                      </div>
                    )}
                    <label className="absolute bottom-0 right-0 p-2 bg-primary rounded-full cursor-pointer hover:bg-primary-dark transition-colors">
                      <Upload className="w-4 h-4" />
                      <input
                        type="file"
                        accept="image/*"
                        className="hidden"
                        onChange={(e) => {
                          const file = e.target.files[0];
                          if (file) setAvatarFile(file);
                        }}
                      />
                    </label>
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-white">{profileName || 'User'}</h3>
                    <p className="text-text-muted">{profileEmail}</p>
                  </div>
                </div>

                {/* Name */}
                <div>
                  <label className="block text-sm font-medium text-white mb-2">Name</label>
                  <input
                    type="text"
                    value={profileName}
                    onChange={(e) => setProfileName(e.target.value)}
                    className="w-full px-4 py-2 bg-black/30 border border-white/10 rounded-lg text-white focus:outline-none focus:border-primary"
                    placeholder="Your name"
                  />
                </div>

                {/* Email (read-only) */}
                <div>
                  <label className="block text-sm font-medium text-white mb-2">Email</label>
                  <input
                    type="email"
                    value={profileEmail}
                    disabled
                    className="w-full px-4 py-2 bg-black/20 border border-white/10 rounded-lg text-text-muted cursor-not-allowed"
                  />
                  <p className="text-xs text-text-muted mt-1">Email cannot be changed</p>
                </div>

                <button
                  onClick={handleSaveProfile}
                  disabled={loading}
                  className="flex items-center gap-2 px-6 py-2 bg-primary hover:bg-primary-dark rounded-lg text-white font-medium transition-colors disabled:opacity-50"
                >
                  <Save className="w-4 h-4" />
                  {loading ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            )}

            {/* Notifications Tab */}
            {activeTab === 'notifications' && (
              <div className="space-y-4">
                <p className="text-text-muted">Notification preferences coming soon</p>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 bg-black/20 rounded-lg">
                    <div>
                      <p className="text-white font-medium">Email Notifications</p>
                      <p className="text-sm text-text-muted">Receive email updates</p>
                    </div>
                    <input type="checkbox" disabled className="opacity-50" />
                  </div>
                  <div className="flex items-center justify-between p-4 bg-black/20 rounded-lg">
                    <div>
                      <p className="text-white font-medium">Project Updates</p>
                      <p className="text-sm text-text-muted">Get notified about project changes</p>
                    </div>
                    <input type="checkbox" disabled className="opacity-50" />
                  </div>
                </div>
              </div>
            )}

            {/* Billing Tab */}
            {activeTab === 'billing' && (
              <div className="space-y-4">
                <p className="text-text-muted">Billing management coming soon</p>
                <div className="p-6 bg-black/20 rounded-lg border border-white/10">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <p className="text-white font-medium">Current Plan</p>
                      <p className="text-sm text-text-muted">Free Plan</p>
                    </div>
                    <span className="px-3 py-1 bg-primary/20 text-primary rounded-full text-sm font-medium">
                      Free
                    </span>
                  </div>
                  <button
                    disabled
                    className="w-full px-4 py-2 bg-primary/20 text-primary rounded-lg font-medium opacity-50 cursor-not-allowed"
                  >
                    Upgrade to Pro
                  </button>
                </div>
              </div>
            )}

            {/* LLM Tab */}
            {activeTab === 'llm' && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-white">LLM Configurations</h3>
                  <button
                    onClick={() => setShowAddLLM(!showAddLLM)}
                    className="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary-dark rounded-lg text-white text-sm font-medium transition-colors"
                  >
                    <Plus className="w-4 h-4" />
                    Add LLM
                  </button>
                </div>

                {showAddLLM && (
                  <div className="p-4 bg-black/20 rounded-lg border border-white/10 space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-white mb-2">Provider</label>
                      <select
                        value={newLLM.provider}
                        onChange={(e) => setNewLLM({ ...newLLM, provider: e.target.value })}
                        className="w-full px-4 py-2 bg-black/30 border border-white/10 rounded-lg text-white focus:outline-none focus:border-primary"
                      >
                        <option value="">Select provider</option>
                        <option value="OpenAI">OpenAI</option>
                        <option value="Anthropic">Anthropic</option>
                        <option value="Google">Google</option>
                        <option value="Ollama">Ollama</option>
                        <option value="DeepSeek">DeepSeek</option>
                        <option value="Groq">Groq</option>
                        <option value="Mistral">Mistral</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-white mb-2">Model (Optional)</label>
                      <input
                        type="text"
                        value={newLLM.model}
                        onChange={(e) => setNewLLM({ ...newLLM, model: e.target.value })}
                        className="w-full px-4 py-2 bg-black/30 border border-white/10 rounded-lg text-white focus:outline-none focus:border-primary"
                        placeholder="e.g., gpt-4o"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-white mb-2">API Key</label>
                      <input
                        type="password"
                        value={newLLM.api_key}
                        onChange={(e) => setNewLLM({ ...newLLM, api_key: e.target.value })}
                        className="w-full px-4 py-2 bg-black/30 border border-white/10 rounded-lg text-white focus:outline-none focus:border-primary"
                        placeholder="Enter API key"
                      />
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={handleAddLLM}
                        disabled={loading}
                        className="flex-1 px-4 py-2 bg-primary hover:bg-primary-dark rounded-lg text-white font-medium transition-colors disabled:opacity-50"
                      >
                        {loading ? 'Adding...' : 'Add LLM'}
                      </button>
                      <button
                        onClick={() => {
                          setShowAddLLM(false);
                          setNewLLM({ provider: '', model: '', api_key: '' });
                        }}
                        className="px-4 py-2 bg-black/30 hover:bg-black/50 rounded-lg text-white font-medium transition-colors"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}

                <div className="space-y-2">
                  {llms.length === 0 ? (
                    <p className="text-text-muted text-center py-8">No LLMs configured</p>
                  ) : (
                    llms.map((llm) => (
                      <div
                        key={llm.id}
                        className="flex items-center justify-between p-4 bg-black/20 rounded-lg border border-white/10"
                      >
                        <div>
                          <p className="text-white font-medium">{llm.provider}</p>
                          <p className="text-sm text-text-muted">
                            {llm.is_default && 'Default • '}
                            {llm.is_active ? 'Active' : 'Inactive'}
                          </p>
                        </div>
                        <button
                          onClick={() => handleRemoveLLM(llm.id)}
                          disabled={loading}
                          className="p-2 text-error hover:bg-error/20 rounded-lg transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}

            {/* Danger Zone Tab */}
            {activeTab === 'danger' && (
              <div className="space-y-6">
                <div className="p-6 bg-error/10 border border-error/30 rounded-lg">
                  <div className="flex items-start gap-4">
                    <AlertTriangle className="w-6 h-6 text-error flex-shrink-0 mt-1" />
                    <div>
                      <h3 className="text-lg font-semibold text-error mb-2">Danger Zone</h3>
                      <p className="text-text-muted text-sm">
                        These actions are irreversible. Please be certain before proceeding.
                      </p>
                    </div>
                  </div>
                </div>

                {/* Delete All Projects */}
                <div className="p-6 bg-black/20 rounded-lg border border-white/10">
                  <h4 className="text-white font-medium mb-2">Delete All Projects</h4>
                  <p className="text-sm text-text-muted mb-4">
                    This will permanently delete all your projects. This action cannot be undone.
                  </p>
                  <div className="space-y-3">
                    <input
                      type="text"
                      value={confirmDeleteProjects}
                      onChange={(e) => setConfirmDeleteProjects(e.target.value)}
                      placeholder="Type DELETE to confirm"
                      className="w-full px-4 py-2 bg-black/30 border border-white/10 rounded-lg text-white focus:outline-none focus:border-error"
                    />
                    <button
                      onClick={handleDeleteAllProjects}
                      disabled={loading || confirmDeleteProjects !== 'DELETE'}
                      className="w-full px-4 py-2 bg-error hover:bg-error/80 rounded-lg text-white font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {loading ? 'Deleting...' : 'Delete All Projects'}
                    </button>
                  </div>
                </div>

                {/* Delete Account */}
                <div className="p-6 bg-black/20 rounded-lg border border-error/30">
                  <h4 className="text-error font-medium mb-2">Delete Account</h4>
                  <p className="text-sm text-text-muted mb-4">
                    This will permanently delete your account and all associated data. This action cannot be undone.
                  </p>
                  <div className="space-y-3">
                    <input
                      type="text"
                      value={confirmDeleteAccount}
                      onChange={(e) => setConfirmDeleteAccount(e.target.value)}
                      placeholder="Type DELETE MY ACCOUNT to confirm"
                      className="w-full px-4 py-2 bg-black/30 border border-error/30 rounded-lg text-white focus:outline-none focus:border-error"
                    />
                    <button
                      onClick={handleDeleteAccount}
                      disabled={loading || confirmDeleteAccount !== 'DELETE MY ACCOUNT'}
                      className="w-full px-4 py-2 bg-error hover:bg-error/80 rounded-lg text-white font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {loading ? 'Deleting...' : 'Delete My Account'}
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between gap-2 p-4 sm:p-6 border-t border-white/10">
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 px-4 py-2 text-error hover:bg-error/20 rounded-lg transition-colors"
            >
              <LogOut className="w-4 h-4" />
              Logout
            </button>
            <button
              onClick={onClose}
              className="px-6 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-white font-medium transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </>
  );
};

