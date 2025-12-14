"""
Dynamic project idea collection through intelligent follow-up questions.
"""
import json


class ProjectIdeaCollector:
    """Collects project requirements through smart, adaptive questioning."""
    
    def __init__(self, llm_client, search_engine, storage):
        self.llm = llm_client
        self.search = search_engine
        self.storage = storage
        self.project_info = {}
    
    def start_collection(self):
        """Start project idea collection."""
        return {
            "status": "collection_started",
            "first_question": "Describe your project idea in one sentence:",
            "stage": "initial_idea"
        }
    
    def process_idea(self, user_input, conversation_history=None):
        """
        Process user's project idea and ask intelligent follow-up questions.
        
        Args:
            user_input: User's current response
            conversation_history: Previous Q&A for context
            
        Returns:
            Dict with next question or completion status
        """
        if conversation_history is None:
            conversation_history = []
        
        # Add current input to history
        conversation_history.append({"role": "user", "content": user_input})
        
        # Determine what information we still need
        needed_info = self._analyze_what_we_need(conversation_history)
        
        if needed_info["complete"]:
            # We have everything - finalize project info
            return self._finalize_project_info(conversation_history)
        
        # Generate next intelligent question
        next_question = self._generate_next_question(
            conversation_history,
            needed_info
        )
        
        return {
            "question": next_question,
            "stage": needed_info["current_stage"],
            "complete": False,
            "conversation_history": conversation_history
        }
    
    def _analyze_what_we_need(self, conversation_history):
        """
        Analyze conversation to determine what info is still needed.
        
        Returns:
            Dict with needed info and current stage
        """
        # Build prompt for analysis
        prompt = self._build_analysis_prompt(conversation_history)
        
        # Ask LLM what we're missing
        messages = [
            {
                "role": "system",
                "content": """You are analyzing a project idea conversation.
Determine what critical information is still missing:

- Project type/category
- Target users
- Main features (at least 3)
- Scale/complexity
- Special requirements

Respond in this format:

MISSING:
- [list what's missing]

HAVE:
- [list what we know]

STAGE: [users/features/scale/requirements/complete]

COMPLETE: [yes/no]
"""
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        response = self.llm.chat(messages)
        analysis = response.get("content", "")
        
        # Parse analysis
        missing = []
        have = []
        stage = "initial"
        complete = False
        
        lines = analysis.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if line.startswith("MISSING:"):
                current_section = "missing"
            elif line.startswith("HAVE:"):
                current_section = "have"
            elif line.startswith("STAGE:"):
                stage = line.split(":", 1)[1].strip().lower() if ":" in line else "initial"
            elif line.startswith("COMPLETE:"):
                complete = "yes" in line.lower()
            elif line.startswith("-") and current_section:
                if current_section == "missing":
                    missing.append(line[1:].strip())
                elif current_section == "have":
                    have.append(line[1:].strip())
        
        return {
            "missing": missing,
            "have": have,
            "current_stage": stage,
            "complete": complete
        }
    
    def _build_analysis_prompt(self, conversation_history):
        """Build prompt for analyzing conversation."""
        prompt_parts = ["CONVERSATION SO FAR:"]
        
        for msg in conversation_history:
            role = "User" if msg["role"] == "user" else "Agent"
            prompt_parts.append(f"{role}: {msg['content']}")
        
        prompt_parts.append("\nAnalyze what project information we have and what's missing:")
        
        return "\n".join(prompt_parts)
    
    def _generate_next_question(self, conversation_history, needed_info):
        """
        Generate intelligent next question based on what's missing.
        
        Args:
            conversation_history: Previous conversation
            needed_info: Dict from _analyze_what_we_need
            
        Returns:
            Next question to ask user
        """
        # Extract project idea so far
        project_idea = self._extract_project_idea(conversation_history)
        
        # Search online for context about this type of project
        search_context = ""
        if project_idea:
            try:
                search_results = self.search.search(f"{project_idea} app common features")
                if search_results.get("results"):
                    # Use top result for context
                    top_result = search_results["results"][0]
                    search_context = f"Research shows: {top_result.get('content', '')[:500]}"
            except:
                pass
        
        # Build prompt for next question
        prompt_parts = []
        prompt_parts.append(f"PROJECT IDEA: {project_idea}")
        prompt_parts.append(f"\nWHAT WE HAVE: {', '.join(needed_info['have'])}")
        prompt_parts.append(f"WHAT WE NEED: {', '.join(needed_info['missing'])}")
        prompt_parts.append(f"CURRENT STAGE: {needed_info['current_stage']}")
        
        if search_context:
            prompt_parts.append(f"\nRESEARCH CONTEXT:\n{search_context}")
        
        prompt_parts.append("\nGenerate ONE specific follow-up question to get the most critical missing information.")
        prompt_parts.append("Make it conversational and specific to their project type.")
        
        # Get next question from LLM
        messages = [
            {
                "role": "system",
                "content": """You are asking follow-up questions to understand a project.
Ask ONE question at a time.
Be specific to their project type.
Use simple language.
Make it conversational.

Examples:
- For social media app: "Who can post content - anyone, approved users, or paid members?"
- For e-commerce: "Do you need inventory management or just a product catalog?"
- For tool app: "Should this work offline or require internet?"

Just output the question, nothing else."""
            },
            {
                "role": "user",
                "content": "\n".join(prompt_parts)
            }
        ]
        
        response = self.llm.chat(messages)
        question = response.get("content", "").strip()
        
        return question
    
    def _extract_project_idea(self, conversation_history):
        """Extract the core project idea from conversation."""
        for msg in conversation_history:
            if msg["role"] == "user":
                # First user message is usually the main idea
                return msg["content"]
        return ""
    
    def _finalize_project_info(self, conversation_history):
        """
        Extract and structure all project information from conversation.
        
        Args:
            conversation_history: Complete conversation
            
        Returns:
            Structured project info
        """
        # Build prompt to extract structured data
        conversation_text = "\n".join([
            f"{'User' if msg['role'] == 'user' else 'Agent'}: {msg['content']}"
            for msg in conversation_history
        ])
        
        prompt = f"""Extract structured project information from this conversation:

{conversation_text}

Respond ONLY with JSON in this exact format:

{{
  "idea": "brief project description",
  "users": ["user type 1", "user type 2"],
  "features": ["feature 1", "feature 2", "feature 3"],
  "scale": "simple/medium/large",
  "requirements": ["requirement 1", "requirement 2"]
}}
"""
        
        messages = [
            {
                "role": "system",
                "content": "You extract structured data from conversations. Output ONLY valid JSON, nothing else."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        response = self.llm.chat(messages)
        
        # Parse JSON response
        try:
            # Clean response (remove markdown if present)
            content = response.get("content", "").strip()
            if content.startswith("```"):
                # Remove code fences
                lines = content.split('\n')
                content = '\n'.join(lines[1:-1])
            
            project_info = json.loads(content)
            
            # Save to storage
            self.storage.save("project", project_info)
            
            return {
                "complete": True,
                "project_info": project_info,
                "status": "Project information collected successfully"
            }
            
        except (json.JSONDecodeError, KeyError):
            # Fallback: manual parsing
            return {
                "complete": True,
                "project_info": {
                    "idea": self._extract_project_idea(conversation_history),
                    "users": [],
                    "features": [],
                    "scale": "medium",
                    "requirements": []
                },
                "status": "Project information collected (fallback mode)"
            }

