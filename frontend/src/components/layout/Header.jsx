import React from 'react';
import { ProfileDropdown } from './ProfileDropdown';

export const Header = () => {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-white/10 glass">
      <div className="container flex h-16 items-center px-6">
        {/* Logo */}
        <div className="flex items-center gap-2">
          <div className="text-2xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
            BOTUVIC
          </div>
          <div className="text-2xl">🤖</div>
        </div>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Profile Dropdown */}
        <ProfileDropdown />
      </div>
    </header>
  );
};

