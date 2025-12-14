"""
Tech stack decision module - researches and decides optimal tech stack.
"""


class TechStackDecider:
    """Decides tech stack based on project requirements and research."""
    
    def __init__(self, llm_client, search_engine, storage):
        self.llm = llm_client
        self.search = search_engine
        self.storage = storage
    
    def decide_stack(self, project_info, user_profile):
        """
        Research and decide complete tech stack.
        
        Args:
            project_info: Dict with project details
            user_profile: Dict with user skill level
            
        Returns:
            Dict with decided tech stack and reasoning
        """
        # Step 1: Research online for this type of project
        research_results = self._research_tech_options(project_info)
        
        # Step 2: Make decision based on research + user profile
        tech_stack = self._make_decision(
            project_info,
            user_profile,
            research_results
        )
        
        # Step 3: Lock the decision
        tech_stack["locked"] = True
        
        # Step 4: Save to storage
        project_info["tech_stack"] = tech_stack
        self.storage.save("project", project_info)
        
        return tech_stack
    
    def _research_tech_options(self, project_info):
        """Research tech stack options online."""
        idea = project_info.get("idea", "")
        scale = project_info.get("scale", "medium")
        
        # Build search queries
        queries = [
            f"best tech stack for {idea}",
            f"{idea} proven architecture",
            f"{idea} technology recommendations {scale} scale"
        ]
        
        research = {
            "queries": queries,
            "results": []
        }
        
        # Search for each query
        for query in queries:
            try:
                search_result = self.search.search(query)
                if search_result.get("results"):
                    research["results"].extend(search_result["results"][:3])  # Limit to 3 per query
            except:
                continue
        
        return research
    
    def _make_decision(self, project_info, user_profile, research):
        """
        Make tech stack decision based on all factors.
        
        Args:
            project_info: Project details
            user_profile: User skill level
            research: Research results from web
            
        Returns:
            Tech stack dict
        """
        # Build decision prompt
        prompt = self._build_decision_prompt(project_info, user_profile, research)
        
        # Get decision from LLM
        messages = [
            {
                "role": "system",
                "content": self._get_decision_system_prompt()
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        response = self.llm.chat(messages)
        decision_text = response.get("content", "")
        
        # Parse decision
        tech_stack = self._parse_decision(decision_text, project_info)
        
        return tech_stack
    
    def _get_decision_system_prompt(self):
        """System prompt for tech stack decision."""
        return """You are a senior software architect deciding tech stacks.

Consider:
1. Project requirements (features, scale, users)
2. User skill level (beginner/intermediate/expert)
3. Research findings (what works for this type of project)
4. Ease of development vs performance needs
5. Community support and resources

For beginners: Choose popular, well-documented, easy-to-learn tech
For experts: Can choose more advanced but powerful options

Respond in this format:

TECH STACK DECISION:

Frontend: [technology]
Reason: [why this is best choice]

Backend: [technology]
Reason: [why this is best choice]

Database: [technology]
Reason: [why this is best choice]

[Add other components as needed: Auth, Storage, Deployment, etc.]

OVERALL REASONING:
[Why this stack works together for this project]
"""
    
    def _build_decision_prompt(self, project_info, user_profile, research):
        """Build prompt for tech stack decision."""
        prompt_parts = []
        
        # Project info
        prompt_parts.append("PROJECT:")
        prompt_parts.append(f"- Idea: {project_info.get('idea', 'Unknown')}")
        prompt_parts.append(f"- Users: {', '.join(project_info.get('users', []))}")
        prompt_parts.append(f"- Features: {', '.join(project_info.get('features', []))}")
        prompt_parts.append(f"- Scale: {project_info.get('scale', 'medium')}")
        
        if project_info.get('requirements'):
            prompt_parts.append(f"- Requirements: {', '.join(project_info['requirements'])}")
        
        # User profile
        prompt_parts.append("\nUSER PROFILE:")
        prompt_parts.append(f"- Experience: {user_profile.get('experience', 'unknown')}")
        prompt_parts.append(f"- Coding ability: {user_profile.get('coding_ability', 'unknown')}")
        
        tech_knowledge = user_profile.get('tech_knowledge', [])
        if tech_knowledge and 'none' not in tech_knowledge:
            prompt_parts.append(f"- Knows: {', '.join(tech_knowledge)}")
        else:
            prompt_parts.append("- Tech knowledge: None")
        
        # Research findings
        prompt_parts.append("\nRESEARCH FINDINGS:")
        for i, result in enumerate(research.get("results", [])[:5], 1):
            prompt_parts.append(f"\n{i}. {result.get('title', 'Result')}")
            content = result.get('content', '')[:300]
            prompt_parts.append(f"   {content}...")
        
        prompt_parts.append("\nDecide the optimal tech stack:")
        
        return "\n".join(prompt_parts)
    
    def _parse_decision(self, decision_text, project_info):
        """Parse LLM decision into structured format."""
        tech_stack = {
            "frontend": None,
            "backend": None,
            "database": None,
            "auth": None,
            "storage": None,
            "deployment": None,
            "reasoning": {},
            "overall_reasoning": ""
        }
        
        lines = decision_text.split('\n')
        current_component = None
        
        for line in lines:
            line = line.strip()
            
            # Parse component decisions
            if line.startswith("Frontend:"):
                tech_stack["frontend"] = line.split(":", 1)[1].strip() if ":" in line else None
                current_component = "frontend"
            elif line.startswith("Backend:"):
                tech_stack["backend"] = line.split(":", 1)[1].strip() if ":" in line else None
                current_component = "backend"
            elif line.startswith("Database:"):
                tech_stack["database"] = line.split(":", 1)[1].strip() if ":" in line else None
                current_component = "database"
            elif line.startswith("Auth:") or line.startswith("Authentication:"):
                tech_stack["auth"] = line.split(":", 1)[1].strip() if ":" in line else None
                current_component = "auth"
            elif line.startswith("Storage:"):
                tech_stack["storage"] = line.split(":", 1)[1].strip() if ":" in line else None
                current_component = "storage"
            elif line.startswith("Deployment:"):
                tech_stack["deployment"] = line.split(":", 1)[1].strip() if ":" in line else None
                current_component = "deployment"
            
            # Parse reasoning
            elif line.startswith("Reason:") and current_component:
                reason = line.split(":", 1)[1].strip() if ":" in line else ""
                tech_stack["reasoning"][current_component] = reason
            
            # Parse overall reasoning
            elif line.startswith("OVERALL REASONING:"):
                current_component = "overall"
            elif current_component == "overall" and line:
                tech_stack["overall_reasoning"] += line + " "
        
        # Clean up
        tech_stack["overall_reasoning"] = tech_stack["overall_reasoning"].strip()
        
        # Remove None values
        tech_stack = {k: v for k, v in tech_stack.items() if v is not None}
        
        return tech_stack
    
    def get_tech_stack(self):
        """Get saved tech stack from storage."""
        project = self.storage.load("project")
        if project:
            return project.get("tech_stack")
        return None

