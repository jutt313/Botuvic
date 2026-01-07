import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import { authService } from '@/services/auth';
import { CheckCircle2, ChevronRight, Sparkles } from 'lucide-react';
import './Onboarding.css';

const QUESTIONS = [
  {
    id: 'experience_level',
    question: 'Are you a professional developer, learning to code, or new to tech?',
    type: 'single',
    required: true,
    options: [
      { value: 'professional', label: 'Professional Developer' },
      { value: 'learning', label: 'Learning to Code' },
      { value: 'non-technical', label: 'New to Tech' },
    ],
  },
  {
    id: 'tech_knowledge',
    question: 'What do you know? (Pick all that apply)',
    type: 'multiple',
    required: true,
    options: [
      { value: 'frontend', label: 'Frontend (React, HTML, CSS)' },
      { value: 'backend', label: 'Backend (Node, Python, APIs)' },
      { value: 'databases', label: 'Databases (SQL, MongoDB)' },
      { value: 'mobile', label: 'Mobile Development' },
      { value: 'none', label: 'None of the above' },
    ],
  },
  {
    id: 'coding_ability',
    question: 'How much can you code yourself?',
    type: 'single',
    required: true,
    options: [
      { value: 'from_scratch', label: 'Write code from scratch' },
      { value: 'modify', label: 'Modify existing code' },
      { value: 'tutorials', label: 'Follow tutorials' },
      { value: 'none', label: "Can't code yet" },
    ],
  },
  {
    id: 'tool_preference',
    question: 'For projects, do you want to:',
    type: 'single',
    required: true,
    options: [
      { value: 'user_choice', label: 'Choose your own tools and frameworks' },
      { value: 'agent_decides', label: 'Let me recommend based on best practices' },
    ],
  },
  {
    id: 'help_level',
    question: 'How much guidance do you need?',
    type: 'single',
    required: true,
    options: [
      { value: 'minimal', label: 'Minimal - just build it' },
      { value: 'explain', label: 'Explain as you go' },
      { value: 'maximum', label: 'Maximum - teach me everything' },
    ],
  },
  {
    id: 'ai_tools',
    question: 'Which AI coding tools will you use? (Pick all that apply)',
    type: 'multiple',
    required: true,
    options: [
      { value: 'cursor', label: 'Cursor' },
      { value: 'copilot', label: 'GitHub Copilot' },
      { value: 'claude_code', label: 'Claude Code (Cline)' },
      { value: 'v0', label: 'v0.dev' },
      { value: 'bolt', label: 'Bolt.new' },
      { value: 'none', label: 'None - coding manually' },
    ],
  },
  {
    id: 'primary_goal',
    question: "What's your main goal?",
    type: 'single',
    required: false,
    options: [
      { value: 'learn', label: 'Learn to code while building' },
      { value: 'build_product', label: 'Build product to launch' },
      { value: 'experimenting', label: 'Just experimenting/hobby' },
      { value: 'portfolio', label: 'Build for portfolio' },
    ],
  },
  {
    id: 'time_commitment',
    question: 'How much time can you dedicate?',
    type: 'single',
    required: false,
    options: [
      { value: 'full_time', label: 'Full-time (30+ hrs/week)' },
      { value: 'part_time', label: 'Part-time (10-20 hrs/week)' },
      { value: 'weekends', label: 'Weekends only (5-10 hrs/week)' },
      { value: 'casual', label: 'Casual (few hours/week)' },
    ],
  },
  {
    id: 'team_or_solo',
    question: 'Are you:',
    type: 'single',
    required: false,
    options: [
      { value: 'solo', label: 'Building solo' },
      { value: 'team', label: 'Working with a team' },
      { value: 'hire_later', label: 'Planning to hire developers later' },
    ],
  },
  {
    id: 'previous_projects',
    question: 'Have you built apps before?',
    type: 'single',
    required: false,
    options: [
      { value: 'multiple', label: 'Yes, multiple projects' },
      { value: 'one_two', label: 'Yes, one or two' },
      { value: 'none', label: "No, this is my first" },
      { value: 'started_never_finished', label: 'Started but never finished' },
    ],
  },
];

export default function Onboarding() {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const currentQuestion = QUESTIONS[currentQuestionIndex];
  const isRequired = currentQuestion.required;
  const isLastQuestion = currentQuestionIndex === QUESTIONS.length - 1;
  const progress = ((currentQuestionIndex + 1) / QUESTIONS.length) * 100;

  // Check if user is authenticated and if profile is already complete
  useEffect(() => {
    const checkProfile = async () => {
      if (!user) {
        navigate('/login');
        return;
      }

      // Wait a bit for user to load
      await new Promise(resolve => setTimeout(resolve, 300));

      try {
        const userProfile = await authService.getCurrentUser();
        const isProfileComplete = userProfile.experience_level && 
                                  userProfile.tech_knowledge && 
                                  userProfile.coding_ability && 
                                  userProfile.tool_preference && 
                                  userProfile.help_level && 
                                  userProfile.ai_tools;

        if (isProfileComplete) {
          // Profile already complete, redirect to dashboard
          navigate('/');
        }
      } catch (error) {
        console.error('Failed to check profile:', error);
        // Continue with onboarding if check fails
      }
    };

    checkProfile();
  }, [user, navigate]);

  const handleAnswer = (value) => {
    if (currentQuestion.type === 'single') {
      setAnswers({ ...answers, [currentQuestion.id]: value });
    } else {
      // Multiple selection
      const currentValues = answers[currentQuestion.id] || [];
      const newValues = currentValues.includes(value)
        ? currentValues.filter((v) => v !== value)
        : [...currentValues, value];
      setAnswers({ ...answers, [currentQuestion.id]: newValues });
    }
  };

  const canProceed = () => {
    if (!isRequired) return true;
    const answer = answers[currentQuestion.id];
    if (currentQuestion.type === 'multiple') {
      return Array.isArray(answer) && answer.length > 0;
    }
    return answer !== undefined && answer !== '';
  };

  const handleNext = () => {
    if (!canProceed()) {
      setError('Please select an option');
      return;
    }
    setError('');

    if (isLastQuestion) {
      handleSubmit();
    } else {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    }
  };

  const handleBack = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1);
      setError('');
    }
  };

  const handleSubmit = async () => {
    if (!canProceed()) {
      setError('Please answer this question');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Prepare profile data
      const profileData = {
        experience_level: answers.experience_level,
        tech_knowledge: answers.tech_knowledge || [],
        coding_ability: answers.coding_ability,
        tool_preference: answers.tool_preference,
        help_level: answers.help_level,
        ai_tools: answers.ai_tools || [],
        primary_goal: answers.primary_goal || null,
        time_commitment: answers.time_commitment || null,
        team_or_solo: answers.team_or_solo || null,
        previous_projects: answers.previous_projects || null,
      };

      // Save profile
      const updatedUser = await authService.updateProfile(profileData);

      // Update auth store with new user data
      useAuthStore.getState().updateUser(updatedUser);

      // Redirect to dashboard
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to save profile');
    } finally {
      setLoading(false);
    }
  };

  const getCurrentAnswer = () => {
    return answers[currentQuestion.id];
  };

  const isSelected = (value) => {
    if (currentQuestion.type === 'single') {
      return getCurrentAnswer() === value;
    } else {
      const currentValues = answers[currentQuestion.id] || [];
      return currentValues.includes(value);
    }
  };

  if (!user) {
    return null;
  }

  return (
    <div className="onboarding-container">
      <div className="onboarding-content">
        {/* Progress Bar */}
        <div className="onboarding-progress">
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${progress}%` }}
            />
          </div>
          <div className="progress-text">
            Question {currentQuestionIndex + 1} of {QUESTIONS.length}
          </div>
        </div>

        {/* Question Card */}
        <div className="onboarding-card">
          <div className="question-header">
            <div className="question-icon">
              <Sparkles className="w-8 h-8" />
            </div>
            <h1 className="question-title">{currentQuestion.question}</h1>
            {!isRequired && (
              <span className="optional-badge">Optional</span>
            )}
          </div>

          {error && <div className="error-message">{error}</div>}

          <div className="options-container">
            {currentQuestion.options.map((option) => (
              <button
                key={option.value}
                onClick={() => handleAnswer(option.value)}
                className={`option-button ${isSelected(option.value) ? 'selected' : ''}`}
              >
                <div className="option-content">
                  <span className="option-label">{option.label}</span>
                  {isSelected(option.value) && (
                    <CheckCircle2 className="w-5 h-5 check-icon" />
                  )}
                </div>
              </button>
            ))}
          </div>

          {/* Navigation */}
          <div className="navigation-buttons">
            {currentQuestionIndex > 0 && (
              <button
                onClick={handleBack}
                className="nav-button back-button"
                disabled={loading}
              >
                Back
              </button>
            )}
            <button
              onClick={handleNext}
              className="nav-button next-button"
              disabled={loading || !canProceed()}
            >
              {loading ? (
                'Saving...'
              ) : isLastQuestion ? (
                <>
                  Complete Setup
                  <ChevronRight className="w-4 h-4 ml-2" />
                </>
              ) : (
                <>
                  Next
                  <ChevronRight className="w-4 h-4 ml-2" />
                </>
              )}
            </button>
          </div>
        </div>

        {/* Skip optional questions hint */}
        {!isRequired && (
          <button
            onClick={handleNext}
            className="skip-button"
            disabled={loading}
          >
            Skip this question
          </button>
        )}
      </div>
    </div>
  );
}

