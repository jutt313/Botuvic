"""Web search capability using Tavily API"""

import os
from pathlib import Path
from dotenv import load_dotenv
import requests

# Load .env from multiple possible locations
possible_env_paths = [
    Path(__file__).parent.parent.parent.parent.parent / ".env",  # Root project .env
    Path.cwd() / ".env",  # Current directory
    Path.cwd().parent / ".env",  # Parent directory
]

for env_path in possible_env_paths:
    if env_path.exists():
        load_dotenv(env_path)
        break
else:
    load_dotenv()

class SearchEngine:
    """Web search capability using Tavily API."""
    
    def __init__(self):
        self.api_key = os.getenv("TAVILY_API_KEY")
        self.api_url = "https://api.tavily.com/search"
    
    def search(self, query, max_results=5):
        """
        Search the web.
        
        Args:
            query: Search query string
            max_results: Maximum number of results
            
        Returns:
            List of search results with title, url, content
        """
        if not self.api_key:
            return {"error": "TAVILY_API_KEY not set. Web search disabled."}
        
        try:
            response = requests.post(
                self.api_url,
                json={
                    "api_key": self.api_key,
                    "query": query,
                    "max_results": max_results
                },
                timeout=10
            )
            
            data = response.json()
            
            # Format results
            results = []
            for item in data.get("results", []):
                results.append({
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "content": item.get("content")
                })
            
            return {"results": results}
            
        except Exception as e:
            return {"error": str(e)}

