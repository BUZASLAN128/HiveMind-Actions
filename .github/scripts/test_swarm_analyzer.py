import sys
import pytest
from pathlib import Path

# Add the script directory to the path so we can import swarm_analyzer
sys.path.insert(0, str(Path(__file__).parent))

from swarm_analyzer import build_prompt
from ai_utils import load_prompt_template

@pytest.fixture
def real_template():
    """
    Load the real prompt template from the repository.

    Depends on: .github/prompts/swarm_analyzer.prompt (Real Project File)
    """
    prompt_path = Path(__file__).parent.parent / "prompts" / "swarm_analyzer.prompt"
    if not prompt_path.exists():
        pytest.skip(f"Real prompt file not found at {prompt_path}")
    return load_prompt_template(prompt_path)

def test_build_prompt_happy_path(real_template):
    """Test build_prompt with all fields provided using real template."""
    issue_data = {
        'number': 123,
        'title': 'Test Issue',
        'body': 'This is a test issue body.',
        'comment': 'Please fix this.'
    }
    context = "def foo(): pass"
    rules = "Be nice."

    result = build_prompt(real_template, issue_data, context, rules)

    # Verify key components are present in the formatted result
    assert "Issue Number: 123" in result
    assert "Title: Test Issue" in result
    assert "Description: This is a test issue body." in result
    assert "Please fix this." in result
    assert "def foo(): pass" in result
    assert "Be nice." in result

def test_build_prompt_missing_fields(real_template):
    """Test build_prompt with missing issue data fields (check defaults)."""
    issue_data = {}  # Empty dictionary
    context = "context"
    rules = "rules"

    result = build_prompt(real_template, issue_data, context, rules)

    assert "Issue Number: N/A" in result
    assert "Title: No Title" in result
    assert "Description: No Description" in result
    # Comment default is empty, check header exists but content is empty/missing
    assert "## Triggering Comment (Latest Instruction):" in result

def test_build_prompt_empty_context_rules(real_template):
    """Test build_prompt with empty context and rules."""
    issue_data = {'title': 'Test'}
    context = ""
    rules = ""

    result = build_prompt(real_template, issue_data, context, rules)

    # Verify headers exist
    assert "## Project Context (Code Samples):" in result
    assert "## Project Rules:" in result
    # Verify no unexpected placeholders
    assert "{codebase}" not in result
    assert "{rules}" not in result

def test_build_prompt_special_characters(real_template):
    """Test build_prompt with special characters in input."""
    issue_data = {
        'title': 'Test "Quotes"',
        'body': 'Line 1\nLine 2',
        'comment': 'Special chars: {} []'
    }
    context = "def test():\n    return 'special'"
    rules = "Rule 1"

    result = build_prompt(real_template, issue_data, context, rules)

    assert 'Title: Test "Quotes"' in result
    assert 'Description: Line 1\nLine 2' in result
    assert 'Special chars: {} []' in result
