import sys
import pytest
from pathlib import Path

# Add the script directory to the path so we can import swarm_analyzer
sys.path.insert(0, str(Path(__file__).parent))

from swarm_analyzer import build_prompt

@pytest.fixture
def sample_template():
    return """
Issue Number: {issue_number}
Title: {issue_title}
Body: {issue_body}
Comment: {comment}
Context:
{codebase}
Rules:
{rules}
"""

def test_build_prompt_happy_path(sample_template):
    """Test build_prompt with all fields provided."""
    issue_data = {
        'number': 123,
        'title': 'Test Issue',
        'body': 'This is a test issue body.',
        'comment': 'Please fix this.'
    }
    context = "def foo(): pass"
    rules = "Be nice."

    result = build_prompt(sample_template, issue_data, context, rules)

    expected = """
Issue Number: 123
Title: Test Issue
Body: This is a test issue body.
Comment: Please fix this.
Context:
def foo(): pass
Rules:
Be nice.
"""
    assert result.strip() == expected.strip()

def test_build_prompt_missing_fields(sample_template):
    """Test build_prompt with missing issue data fields (check defaults)."""
    issue_data = {}  # Empty dictionary
    context = "context"
    rules = "rules"

    result = build_prompt(sample_template, issue_data, context, rules)

    assert "Issue Number: N/A" in result
    assert "Title: No Title" in result
    assert "Body: No Description" in result
    # Comment default is empty string, so it should be empty in the output
    # Template has "Comment: {comment}", so it becomes "Comment: "
    assert "Comment: " in result

def test_build_prompt_empty_context_rules(sample_template):
    """Test build_prompt with empty context and rules."""
    issue_data = {'title': 'Test'}
    context = ""
    rules = ""

    result = build_prompt(sample_template, issue_data, context, rules)

    # Check that empty strings are correctly inserted
    # Template: Context:\n{codebase} -> Context:\n
    assert "Context:\n" in result
    assert "Rules:\n" in result

def test_build_prompt_special_characters(sample_template):
    """Test build_prompt with special characters in input."""
    issue_data = {
        'title': 'Test "Quotes"',
        'body': 'Line 1\nLine 2',
        'comment': 'Special chars: {} []'
    }
    context = "def test():\n    return 'special'"
    rules = "Rule 1"

    result = build_prompt(sample_template, issue_data, context, rules)

    assert 'Title: Test "Quotes"' in result
    assert 'Body: Line 1\nLine 2' in result
    assert 'Comment: Special chars: {} []' in result
