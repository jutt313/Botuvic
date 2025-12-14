"""
User onboarding module - collects user profile through 6 questions.
"""

class UserOnboarding:
    """Handles user profile collection through interactive questions."""
    
    def __init__(self, llm_client, storage):
        self.llm = llm_client
        self.storage = storage
        self.profile = {}
    
    def start_onboarding(self):
        """
        Start onboarding flow and return questions.
        This integrates with the agent's conversation flow.
        """
        questions = self.get_all_questions()
        
        return {
            "status": "onboarding_started",
            "total_questions": len(questions),
            "questions": questions
        }
    
    def get_all_questions(self):
        """Define all onboarding questions."""
        return [
            {
                "id": "experience",
                "question": "What's your coding experience?\n1. Professional developer\n2. Learning to code\n3. Non-technical (just ideas)\n\nYour choice (1/2/3):",
                "type": "choice",
                "options": ["professional", "learning", "non-technical"],
                "field": "experience"
            },
            {
                "id": "tech_knowledge",
                "question": "What do you know? (select all - comma separated)\n1. Frontend (React, HTML, CSS)\n2. Backend (Node, Python, APIs)\n3. Databases (SQL, MongoDB)\n4. Mobile development\n5. None of the above\n\nYour choices (e.g., 1,2):",
                "type": "multiple_choice",
                "options": {
                    "1": "frontend",
                    "2": "backend",
                    "3": "databases",
                    "4": "mobile",
                    "5": "none"
                },
                "field": "tech_knowledge"
            },
            {
                "id": "coding_ability",
                "question": "How much can you code yourself?\n1. Write code from scratch\n2. Modify existing code\n3. Follow step-by-step tutorials\n4. I can't code yet\n\nYour choice (1/2/3/4):",
                "type": "choice",
                "options": ["scratch", "modify", "tutorials", "cannot"],
                "field": "coding_ability"
            },
            {
                "id": "tool_preference",
                "question": "Do you have preferred tools/frameworks?\n1. Yes, let me choose\n2. No, you decide for me\n\nYour choice (1/2):",
                "type": "choice",
                "options": ["user_choice", "agent_choice"],
                "field": "tool_preference"
            },
            {
                "id": "help_level",
                "question": "How much guidance do you need?\n1. Minimal - just build it\n2. Explain as you go\n3. Maximum - teach me everything\n\nYour choice (1/2/3):",
                "type": "choice",
                "options": ["minimal", "explain", "maximum"],
                "field": "help_level"
            },
            {
                "id": "ai_tools",
                "question": "Which AI coding tools will you use? (select all - comma separated)\n1. Cursor\n2. GitHub Copilot\n3. Claude Code (Cline)\n4. v0.dev\n5. Bolt.new\n6. None - coding manually\n\nYour choices (e.g., 1,3):",
                "type": "multiple_choice",
                "options": {
                    "1": "cursor",
                    "2": "copilot",
                    "3": "claude_code",
                    "4": "v0.dev",
                    "5": "bolt.new",
                    "6": "manual"
                },
                "field": "ai_tools"
            }
        ]
    
    def process_answer(self, question_id, answer):
        """
        Process user's answer to a question.
        
        Args:
            question_id: Question identifier
            answer: User's answer
            
        Returns:
            Dict with processed result and next question
        """
        questions = {q["id"]: q for q in self.get_all_questions()}
        question = questions.get(question_id)
        
        if not question:
            return {"error": "Invalid question ID"}
        
        # Process based on question type
        if question["type"] == "choice":
            # Single choice
            try:
                choice_num = int(answer.strip())
                if 1 <= choice_num <= len(question["options"]):
                    value = question["options"][choice_num - 1]
                    self.profile[question["field"]] = value
                else:
                    return {"error": "Invalid choice", "question": question}
            except ValueError:
                return {"error": "Please enter a number", "question": question}
        
        elif question["type"] == "multiple_choice":
            # Multiple choices
            try:
                choices = [c.strip() for c in answer.split(",")]
                values = []
                for choice in choices:
                    if choice in question["options"]:
                        values.append(question["options"][choice])
                
                if values:
                    self.profile[question["field"]] = values
                else:
                    return {"error": "Invalid choices", "question": question}
            except:
                return {"error": "Invalid format", "question": question}
        
        # Get next question
        all_questions = self.get_all_questions()
        current_index = next((i for i, q in enumerate(all_questions) if q["id"] == question_id), -1)
        
        if current_index < len(all_questions) - 1:
            next_question = all_questions[current_index + 1]
            return {
                "success": True,
                "profile_updated": True,
                "next_question": next_question,
                "completed": False
            }
        else:
            # Onboarding complete
            self.save_profile()
            return {
                "success": True,
                "profile_updated": True,
                "completed": True,
                "profile": self.profile
            }
    
    def save_profile(self):
        """Save completed profile to storage."""
        self.storage.save("profile", self.profile)
        return self.profile
    
    def get_profile(self):
        """Get current profile from storage."""
        return self.storage.load("profile")

