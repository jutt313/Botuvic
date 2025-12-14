"""
Tests for tech stack decision.
"""

import pytest
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from botuvic.agent.functions.tech_stack import TechStackDecider
from botuvic.agent.utils.storage import Storage
from botuvic.agent.utils.llm import LLMClient
from botuvic.agent.utils.search import SearchEngine


def test_decide_stack():
    """Test tech stack decision."""
    test_dir = "./test_tech_stack"
    storage = Storage(test_dir)
    llm = LLMClient()
    search = SearchEngine()
    decider = TechStackDecider(llm, search, storage)
    
    project_info = {
        "idea": "food delivery app",
        "users": ["customers", "restaurants"],
        "features": ["order", "track", "pay"],
        "scale": "medium"
    }
    
    user_profile = {
        "experience": "learning",
        "coding_ability": "tutorials"
    }
    
    tech_stack = decider.decide_stack(project_info, user_profile)
    
    assert tech_stack.get("frontend") is not None or tech_stack.get("backend") is not None
    assert tech_stack.get("locked") == True
    
    # Cleanup
    if os.path.exists(test_dir):
        import shutil
        shutil.rmtree(test_dir)

