import React, { useState } from 'react';
import { useAuthStore } from '@/store/authStore';
import { User } from 'lucide-react';
import { ProfilePopup } from './ProfilePopup';

export const ProfileDropdown = () => {
  const [isPopupOpen, setIsPopupOpen] = useState(false);
  const { user } = useAuthStore();

  if (!user) {
    return null;
  }

  const getInitials = (name, email) => {
    if (name) {
      return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
    }
    return email ? email[0].toUpperCase() : 'U';
  };

  return (
    <>
      <button
        onClick={() => setIsPopupOpen(true)}
        className="icon-button"
        aria-label="Profile"
      >
        {user.avatar_url ? (
          <img
            src={user.avatar_url}
            alt="Avatar"
            className="w-6 h-6 rounded-full object-cover"
          />
        ) : (
          <div className="w-6 h-6 rounded-full bg-gradient-to-r from-primary to-secondary flex items-center justify-center text-white text-xs font-bold">
            {getInitials(user.name, user.email)}
          </div>
        )}
      </button>

      <ProfilePopup isOpen={isPopupOpen} onClose={() => setIsPopupOpen(false)} />
    </>
  );
};

