import React, { useState, useEffect } from 'react';
import { useAuthStore } from '@/store/authStore';
import { useNavigate } from 'react-router-dom';
import { 
  User, 
  Settings, 
  LogOut, 
  Bot,
  ChevronDown 
} from 'lucide-react';

export const ProfileDropdown = () => {
  const [isOpen, setIsOpen] = useState(false);
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (isOpen && !event.target.closest('.profile-dropdown')) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  if (!user) {
    return null;
  }

  return (
    <div className="relative profile-dropdown">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 rounded-lg px-3 py-2 hover:bg-white/10 transition-colors"
      >
        <div className="w-8 h-8 rounded-full bg-gradient-to-r from-primary to-secondary flex items-center justify-center">
          <User className="w-5 h-5" />
        </div>
        <span className="text-sm font-medium">{user.name || user.email}</span>
        <ChevronDown className="w-4 h-4" />
      </button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />

          {/* Dropdown */}
          <div className="absolute right-0 mt-2 w-56 rounded-lg glass border border-white/10 shadow-lg z-50">
            <div className="p-3 border-b border-white/10">
              <div className="text-sm font-medium">{user.name || 'User'}</div>
              <div className="text-xs text-text-muted">{user.email}</div>
            </div>

            <div className="p-2">
              <button
                onClick={() => {
                  navigate('/settings');
                  setIsOpen(false);
                }}
                className="flex items-center gap-3 w-full rounded-md px-3 py-2 text-sm hover:bg-white/10 transition-colors"
              >
                <Settings className="w-4 h-4" />
                Settings
              </button>

              <button
                onClick={() => {
                  navigate('/settings?tab=llm');
                  setIsOpen(false);
                }}
                className="flex items-center gap-3 w-full rounded-md px-3 py-2 text-sm hover:bg-white/10 transition-colors"
              >
                <Bot className="w-4 h-4" />
                LLM Configuration
              </button>

              <div className="my-2 border-t border-white/10" />

              <button
                onClick={handleLogout}
                className="flex items-center gap-3 w-full rounded-md px-3 py-2 text-sm hover:bg-error/20 text-error transition-colors"
              >
                <LogOut className="w-4 h-4" />
                Logout
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

