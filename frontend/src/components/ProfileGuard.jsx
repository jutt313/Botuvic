import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import { authService } from '@/services/auth';

export const ProfileGuard = ({ children }) => {
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuthStore();
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const checkProfile = async () => {
      if (!isAuthenticated || !user) {
        setChecking(false);
        return;
      }

      try {
        const userProfile = await authService.getCurrentUser();
        const isProfileComplete = userProfile.experience_level && 
                                  userProfile.tech_knowledge && 
                                  userProfile.coding_ability && 
                                  userProfile.tool_preference && 
                                  userProfile.help_level && 
                                  userProfile.ai_tools;

        if (!isProfileComplete) {
          navigate('/onboarding');
        }
      } catch (error) {
        console.error('Profile check failed:', error);
        // If check fails, redirect to onboarding to be safe
        navigate('/onboarding');
      } finally {
        setChecking(false);
      }
    };

    checkProfile();
  }, [user, isAuthenticated, navigate]);

  if (checking) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ 
        background: 'linear-gradient(to top, #000000 0%, #000000 35%, #05020A 45%, #0A0514 55%, #0F0819 65%, #140B1F 75%, #1A0F2E 85%, #1A0F2E 100%)',
        backgroundAttachment: 'fixed'
      }}>
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          <p className="mt-4 text-text-muted">Loading...</p>
        </div>
      </div>
    );
  }

  return children;
};

