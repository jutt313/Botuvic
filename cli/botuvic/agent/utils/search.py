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
        self.tavily_key = os.getenv("TAVILY_API_KEY")
        self.google_key = os.getenv("GOOGLE_SEARCH_API_KEY")
        self.google_cx = os.getenv("GOOGLE_SEARCH_CX")
        
        self.tavily_url = "https://api.tavily.com/search"
        self.google_url = "https://www.googleapis.com/customsearch/v1"
    
    def search(self, query, max_results=5):
        """
        Search the web using Google (Primary) or Tavily (Fallback).
        """
        # Try Google Search first
        if self.google_key and self.google_cx:
            return self._google_search(query, max_results)
            
        # Fallback to Tavily
        if self.tavily_key:
            return self._tavily_search(query, max_results)
            
        return {"error": "No search API keys set (GOOGLE_SEARCH_API_KEY or TAVILY_API_KEY). Search disabled."}

    def _google_search(self, query, max_results=5):
        try:
            response = requests.get(
                self.google_url,
                params={
                    "key": self.google_key,
                    "cx": self.google_cx,
                    "q": query,
                    "num": max_results
                },
                timeout=10
            )
            data = response.json()
            
            if "error" in data:
                return {"error": f"Google Search Error: {data['error'].get('message')}"}
                
            results = []
            for item in data.get("items", []):
                results.append({
                    "title": item.get("title"),
                    "url": item.get("link"),
                    "content": item.get("snippet")
                })
            return {"results": results}
        except Exception as e:
            return {"error": f"Google Search Exception: {str(e)}"}

    def _tavily_search(self, query, max_results=5):
        try:
            response = requests.post(
                self.tavily_url,
                json={
                    "api_key": self.tavily_key,
                    "query": query,
                    "max_results": max_results
                },
                timeout=10
            )
            data = response.json()
            results = []
            for item in data.get("results", []):
                results.append({
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "content": item.get("content")
                })
            return {"results": results}
        except Exception as e:
            return {"error": f"Tavily Search Error: {str(e)}"}

