import React, { useState, useEffect } from 'react';
import { User, Bot, Key, CreditCard, Upload, Save, AlertTriangle, Clock, Eye, EyeOff } from 'lucide-react';
import { useAuthStore } from '@/store/authStore';
import { authService } from '@/services/auth';

export const ProfilePopup = ({ isOpen, onClose }) => {
  const { user, updateUser } = useAuthStore();
  const [activeTab, setActiveTab] = useState('profile');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Profile state
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [avatarUrl, setAvatarUrl] = useState('');
  const [avatarFile, setAvatarFile] = useState(null);
  
  // Password state
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPasswords, setShowPasswords] = useState(false);
  
  // Sessions state
  const [sessions, setSessions] = useState([]);
  
  // Danger zone state
  const [confirmDeleteProjects, setConfirmDeleteProjects] = useState('');
  const [confirmDeleteAccount, setConfirmDeleteAccount] = useState('');

  useEffect(() => {
    if (isOpen && user) {
      setName(user.name || '');
      setEmail(user.email || '');
      setAvatarUrl(user.avatar_url || '');
      loadSessions();
    }
  }, [isOpen, user]);

  const loadSessions = async () => {
    try {
      const data = await authService.getSessions();
      setSessions(data.sessions || []);
    } catch (err) {
      console.error('Failed to load sessions:', err);
    }
  };

  const handleSaveProfile = async () => {
    setLoading(true);
    setError('');
    setSuccess('');
    
    try {
      let finalAvatarUrl = avatarUrl;
      if (avatarFile) {
        // For now, use object URL - in production, upload to Supabase Storage
        finalAvatarUrl = URL.createObjectURL(avatarFile);
      }
      
      const updated = await authService.updateProfile({
        name,
        avatar_url: finalAvatarUrl,
      });
      
      updateUser(updated);
      setSuccess('Profile updated!');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  const handleChangePassword = async () => {
    if (newPassword !== confirmPassword) {
      setError('New passwords do not match');
      return;
    }
    
    if (newPassword.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }
    
    setLoading(true);
    setError('');
    setSuccess('');
    
    try {
      await authService.changePassword(currentPassword, newPassword);
      setSuccess('Password changed successfully!');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to change password');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAllProjects = async () => {
    if (confirmDeleteProjects !== 'DELETE') {
      setError('Type DELETE to confirm');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      await authService.deleteAllProjects();
      setSuccess('All projects deleted!');
      setConfirmDeleteProjects('');
      setTimeout(() => {
        window.location.reload();
      }, 1500);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete projects');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (confirmDeleteAccount !== 'DELETE MY ACCOUNT') {
      setError('Type DELETE MY ACCOUNT to confirm');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      await authService.deleteAccount();
      // Logout will happen automatically via API redirect
      window.location.href = '/login';
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete account');
      setLoading(false);
    }
  };

  const getInitials = (name, email) => {
    if (name) return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
    return email ? email[0].toUpperCase() : 'U';
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (!isOpen) return null;

  const tabs = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'llm', label: 'LLM', icon: Bot },
    { id: 'mcp', label: 'MCP API', icon: Key },
    { id: 'billing', label: 'Billing', icon: CreditCard },
  ];

  const hasOnboardingData = user?.experience_level || user?.tech_knowledge?.length > 0;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50"
        onClick={onClose}
      />

      {/* Popup - Fixed size, glass, no borders */}
      <div className="fixed inset-0 flex items-center justify-center z-50 p-4">
        <div 
          className="w-[700px] h-[650px] rounded-2xl backdrop-blur-xl bg-white/5 shadow-2xl flex flex-col"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="px-6 py-4">
            <h2 className="text-xl font-semibold text-white">Profile</h2>
          </div>

          {/* Tabs */}
          <div className="flex gap-2 px-6 pb-4">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    activeTab === tab.id
                      ? 'bg-purple-600 text-white'
                      : 'text-white/60 hover:text-white hover:bg-white/10'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </button>
              );
            })}
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto px-6 pb-6 space-y-6">
            {error && (
              <div className="px-4 py-2 bg-red-500/20 border border-red-500/30 rounded-lg text-red-400 text-sm">
                {error}
              </div>
            )}
            {success && (
              <div className="px-4 py-2 bg-green-500/20 border border-green-500/30 rounded-lg text-green-400 text-sm">
                {success}
              </div>
            )}

            {/* ========== PROFILE TAB ========== */}
            {activeTab === 'profile' && (
              <>
                {/* Avatar */}
                <div className="flex justify-center">
                  <div className="relative">
                    {avatarUrl || avatarFile ? (
                      <img
                        src={avatarFile ? URL.createObjectURL(avatarFile) : avatarUrl}
                        alt="Avatar"
                        className="w-24 h-24 rounded-full object-cover border-2 border-purple-500/50"
                      />
                    ) : (
                      <div className="w-24 h-24 rounded-full bg-gradient-to-br from-purple-600 to-cyan-500 flex items-center justify-center text-white text-2xl font-bold">
                        {getInitials(name, email)}
                      </div>
                    )}
                    <label className="absolute -bottom-1 -right-1 p-2 bg-purple-600 rounded-full cursor-pointer hover:bg-purple-500 transition-colors">
                      <Upload className="w-4 h-4 text-white" />
                      <input
                        type="file"
                        accept="image/*"
                        className="hidden"
                        onChange={(e) => e.target.files[0] && setAvatarFile(e.target.files[0])}
                      />
                    </label>
                  </div>
                </div>

                {/* Name */}
                <div>
                  <label className="block text-sm font-medium text-white/70 mb-2">Name</label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-purple-500"
                    placeholder="Your name"
                  />
                </div>

                {/* Email */}
                <div>
                  <label className="block text-sm font-medium text-white/70 mb-2">Email</label>
                  <input
                    type="email"
                    value={email}
                    disabled
                    className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white/50 cursor-not-allowed"
                  />
                </div>

                {/* Password Change */}
                <div className="space-y-3">
                  <label className="block text-sm font-medium text-white/70">Change Password</label>
                  <div className="space-y-3">
                    <div className="relative">
                      <input
                        type={showPasswords ? 'text' : 'password'}
                        value={currentPassword}
                        onChange={(e) => setCurrentPassword(e.target.value)}
                        className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-purple-500 pr-10"
                        placeholder="Current password"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPasswords(!showPasswords)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-white/50 hover:text-white/80"
                      >
                        {showPasswords ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                    <input
                      type={showPasswords ? 'text' : 'password'}
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-purple-500"
                      placeholder="New password"
                    />
                    <input
                      type={showPasswords ? 'text' : 'password'}
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-purple-500"
                      placeholder="Confirm new password"
                    />
                  </div>
                  <button
                    onClick={handleChangePassword}
                    disabled={loading || !currentPassword || !newPassword || !confirmPassword}
                    className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-white text-sm font-medium transition-colors disabled:opacity-50"
                  >
                    Change Password
                  </button>
                </div>

                {/* Onboarding Data */}
                {hasOnboardingData && (
                  <div className="space-y-3 pt-4 border-t border-white/10">
                    <label className="block text-sm font-medium text-white/70">Onboarding Info</label>
                    <div className="space-y-2 text-sm text-white/60">
                      {user.experience_level && (
                        <div><span className="text-white/80">Experience:</span> {user.experience_level}</div>
                      )}
                      {user.tech_knowledge && user.tech_knowledge.length > 0 && (
                        <div><span className="text-white/80">Tech:</span> {user.tech_knowledge.join(', ')}</div>
                      )}
                      {user.coding_ability && (
                        <div><span className="text-white/80">Coding:</span> {user.coding_ability}</div>
                      )}
                      {user.primary_goal && (
                        <div><span className="text-white/80">Goal:</span> {user.primary_goal}</div>
                      )}
                    </div>
                  </div>
                )}

                {/* Auth Sessions */}
                <div className="space-y-3 pt-4 border-t border-white/10">
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-white/70" />
                    <label className="text-sm font-medium text-white/70">Auth Sessions</label>
                  </div>
                  <div className="space-y-2 max-h-32 overflow-y-auto">
                    {sessions.length > 0 ? (
                      sessions.map((session) => (
                        <div key={session.id} className="px-3 py-2 bg-white/5 rounded-lg text-xs">
                          <div className="text-white/80">
                            {session.device_info?.device || session.user_agent || 'Unknown Device'}
                          </div>
                          <div className="text-white/40 mt-1">
                            Created: {formatDate(session.created_at)} • Expires: {formatDate(session.expires_at)}
                          </div>
                        </div>
                      ))
                    ) : (
                      <p className="text-white/40 text-sm text-center py-2">No active sessions</p>
                    )}
                  </div>
                </div>

                {/* Danger Zone */}
                <div className="space-y-4 pt-4 border-t border-red-500/20">
                  <div className="flex items-center gap-2 text-red-400">
                    <AlertTriangle className="w-4 h-4" />
                    <label className="text-sm font-medium">Danger Zone</label>
                  </div>
                  
                  {/* Delete All Projects */}
                  <div className="space-y-2">
                    <p className="text-sm text-white/60">Delete all projects</p>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={confirmDeleteProjects}
                        onChange={(e) => setConfirmDeleteProjects(e.target.value)}
                        placeholder="Type DELETE"
                        className="flex-1 px-3 py-2 bg-white/5 border border-red-500/30 rounded-lg text-white text-sm focus:outline-none"
                      />
                      <button
                        onClick={handleDeleteAllProjects}
                        disabled={loading || confirmDeleteProjects !== 'DELETE'}
                        className="px-4 py-2 bg-red-600 hover:bg-red-500 rounded-lg text-white text-sm font-medium transition-colors disabled:opacity-50"
                      >
                        Delete
                      </button>
                    </div>
                  </div>

                  {/* Delete Account */}
                  <div className="space-y-2">
                    <p className="text-sm text-white/60">Delete account permanently</p>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={confirmDeleteAccount}
                        onChange={(e) => setConfirmDeleteAccount(e.target.value)}
                        placeholder="Type DELETE MY ACCOUNT"
                        className="flex-1 px-3 py-2 bg-white/5 border border-red-500/30 rounded-lg text-white text-sm focus:outline-none"
                      />
                      <button
                        onClick={handleDeleteAccount}
                        disabled={loading || confirmDeleteAccount !== 'DELETE MY ACCOUNT'}
                        className="px-4 py-2 bg-red-600 hover:bg-red-500 rounded-lg text-white text-sm font-medium transition-colors disabled:opacity-50"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </div>

                {/* Save Button */}
                <button
                  onClick={handleSaveProfile}
                  disabled={loading}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-purple-600 hover:bg-purple-500 rounded-lg text-white font-medium transition-colors disabled:opacity-50"
                >
                  <Save className="w-4 h-4" />
                  {loading ? 'Saving...' : 'Save Changes'}
                </button>
              </>
            )}

            {/* ========== OTHER TABS ========== */}
            {activeTab === 'llm' && (
              <div className="text-white/60">LLM section - Coming soon</div>
            )}
            
            {activeTab === 'mcp' && (
              <div className="text-white/60">MCP API section - Coming soon</div>
            )}
            
            {activeTab === 'billing' && (
              <div className="text-white/60">Billing section - Coming soon</div>
            )}
          </div>
        </div>
      </div>
    </>
  );
};
