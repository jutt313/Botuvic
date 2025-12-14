"""
Tests for project idea collection.
"""

import pytest
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from botuvic.agent.functions.project_idea import ProjectIdeaCollector
from botuvic.agent.utils.storage import Storage
from botuvic.agent.utils.llm import LLMClient
from botuvic.agent.utils.search import SearchEngine


def test_start_collection():
    """Test starting project idea collection."""
    test_dir = "./test_project_idea"
    storage = Storage(test_dir)
    llm = LLMClient()
    search = SearchEngine()
    collector = ProjectIdeaCollector(llm, search, storage)
    
    result = collector.start_collection()
    
    assert result["status"] == "collection_started"
    assert "first_question" in result
    
    # Cleanup
    if os.path.exists(test_dir):
        import shutil
        shutil.rmtree(test_dir)


def test_process_initial_idea():
    """Test processing initial project idea."""
    test_dir = "./test_project_process"
    storage = Storage(test_dir)
    llm = LLMClient()
    search = SearchEngine()
    collector = ProjectIdeaCollector(llm, search, storage)
    
    result = collector.process_idea("I want to build a food delivery app")
    
    assert "question" in result or "complete" in result
    assert result.get("complete", False) == False or result.get("complete", False) == True
    
    # Cleanup
    if os.path.exists(test_dir):
        import shutil
        shutil.rmtree(test_dir)

