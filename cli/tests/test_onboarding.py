"""
Tests for user onboarding module.
"""

import pytest
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from botuvic.agent.functions.onboarding import UserOnboarding
from botuvic.agent.utils.storage import Storage
from botuvic.agent.utils.llm import LLMClient


def test_onboarding_questions():
    """Test that all 6 questions are defined."""
    test_dir = "./test_project_onboarding"
    storage = Storage(test_dir)
    llm = LLMClient()
    onboarding = UserOnboarding(llm, storage)
    
    questions = onboarding.get_all_questions()
    
    assert len(questions) == 6
    assert questions[0]["id"] == "experience"
    assert questions[5]["id"] == "ai_tools"
    
    # Cleanup
    if os.path.exists(test_dir):
        import shutil
        shutil.rmtree(test_dir)


def test_process_single_choice():
    """Test processing single choice answer."""
    test_dir = "./test_project_choice"
    storage = Storage(test_dir)
    llm = LLMClient()
    onboarding = UserOnboarding(llm, storage)
    
    result = onboarding.process_answer("experience", "2")
    
    assert result["success"] == True
    assert onboarding.profile["experience"] == "learning"
    assert result["completed"] == False
    
    # Cleanup
    if os.path.exists(test_dir):
        import shutil
        shutil.rmtree(test_dir)


def test_process_multiple_choice():
    """Test processing multiple choice answer."""
    test_dir = "./test_project_multiple"
    storage = Storage(test_dir)
    llm = LLMClient()
    onboarding = UserOnboarding(llm, storage)
    
    result = onboarding.process_answer("ai_tools", "1,3")
    
    assert "cursor" in onboarding.profile["ai_tools"]
    assert "claude_code" in onboarding.profile["ai_tools"]
    
    # Cleanup
    if os.path.exists(test_dir):
        import shutil
        shutil.rmtree(test_dir)


def test_complete_onboarding():
    """Test completing full onboarding flow."""
    test_dir = "./test_project_complete"
    storage = Storage(test_dir)
    llm = LLMClient()
    onboarding = UserOnboarding(llm, storage)
    
    answers = {
        "experience": "2",
        "tech_knowledge": "1,2",
        "coding_ability": "3",
        "tool_preference": "2",
        "help_level": "2",
        "ai_tools": "1"
    }
    
    for question_id, answer in answers.items():
        result = onboarding.process_answer(question_id, answer)
    
    assert result["completed"] == True
    assert "profile" in result
    
    # Cleanup
    if os.path.exists(test_dir):
        import shutil
        shutil.rmtree(test_dir)

