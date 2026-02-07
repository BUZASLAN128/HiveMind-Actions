import pytest
import sys
import os

# Add the current directory to sys.path to import ai_utils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_utils import parse_json_response

def test_parse_json_response_direct_json():
    """Test valid JSON parsing."""
    result = parse_json_response('{"approved": true, "score": 8}')
    assert result['approved'] is True
    assert result['score'] == 8

def test_parse_json_response_markdown_json():
    """Test JSON wrapped in markdown code block."""
    md = '```json\n{"should_proceed": true, "issue_type": "code_request"}\n```'
    result = parse_json_response(md)
    assert result['should_proceed'] is True

def test_parse_json_regex_extraction():
    """Test extracting JSON from text."""
    messy = 'Here is the result: {"score": 7, "approved": false} Thanks!'
    result = parse_json_response(messy)
    assert result['score'] == 7
    assert result['approved'] is False

def test_parse_json_response_nested_json():
    """Test nested JSON parsing."""
    nested = '{"data": {"items": [1, 2, 3]}, "count": 3}'
    result = parse_json_response(nested)
    assert result['count'] == 3
    assert result['data']['items'] == [1, 2, 3]

def test_parse_json_response_raises_value_error():
    """Test that ValueError is raised for invalid JSON."""
    invalid_json = "This is just some random text without any JSON structure."

    with pytest.raises(ValueError, match="Could not parse JSON from response"):
        parse_json_response(invalid_json)

def test_parse_json_response_empty_string():
    """Test that empty string raises ValueError."""
    with pytest.raises(ValueError, match="Could not parse JSON from response"):
        parse_json_response("")

def test_parse_json_response_malformed_json():
    """Test malformed JSON that cannot be repaired."""
    malformed = '{ "key": "value" '  # Missing closing brace

    with pytest.raises(ValueError, match="Could not parse JSON from response"):
        parse_json_response(malformed)
