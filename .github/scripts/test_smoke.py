#!/usr/bin/env python3
"""Smoke tests for HiveMind AI Utils"""
import sys
import os
sys.path.insert(0, '.')

from ai_utils import parse_json_response, with_retry, redact_sensitive_data, load_rules

def test_json_parsing():
    print("=== JSON PARSING TESTS ===")
    
    # Test 1: Direct JSON
    result = parse_json_response('{"approved": true, "score": 8}')
    assert result['approved'] == True
    assert result['score'] == 8
    print("Test 1 PASSED: Direct JSON")
    
    # Test 2: Markdown wrapped
    md = '```json\n{"should_proceed": true, "issue_type": "code_request"}\n```'
    result = parse_json_response(md)
    assert result['should_proceed'] == True
    print("Test 2 PASSED: Markdown JSON")
    
    # Test 3: Text with JSON
    messy = 'Here is the result: {"score": 7, "approved": false} Thanks!'
    result = parse_json_response(messy)
    assert result['score'] == 7
    print("Test 3 PASSED: Regex extraction")
    
    # Test 4: Nested JSON
    nested = '{"data": {"items": [1, 2, 3]}, "count": 3}'
    result = parse_json_response(nested)
    assert result['count'] == 3
    print("Test 4 PASSED: Nested JSON")
    
    print("All JSON tests PASSED!\n")

def test_retry_logic():
    print("=== RETRY LOGIC TESTS ===")
    
    call_count = 0
    def flaky():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError(f"Fail {call_count}")
        return "success"
    
    result = with_retry(flaky, max_retries=3, base_delay=0.05)
    assert result == "success"
    assert call_count == 3
    print(f"Test PASSED: Succeeded after {call_count} attempts")
    print("All retry tests PASSED!\n")

def test_redaction():
    print("=== REDACTION TESTS ===")
    
    tests = [
        ("sk-abc123def456ghi789jkl012mno", "[REDACTED_OPENAI_KEY]"),
        ("ghp_abcdefghij1234567890abcdefghij123456", "[REDACTED_GITHUB_TOKEN]"),
        ("password=secret123", "[REDACTED]"),
    ]
    
    for text, marker in tests:
        result = redact_sensitive_data(text)
        assert marker in result, f"Failed: {text}"
        print(f"PASSED: {marker}")
    
    print("All redaction tests PASSED!\n")

def test_approval_logic():
    print("=== APPROVAL LOGIC TESTS ===")
    
    # Import from swarm_reviewer
    sys.path.insert(0, '.')
    from swarm_reviewer import calculate_approval
    
    # Test 1: High score = approve
    approved, reason = calculate_approval({"score": 9, "security_ok": True})
    assert approved == True
    print("Test 1 PASSED: Score 9 approved")
    
    # Test 2: Low score = reject
    approved, reason = calculate_approval({"score": 4, "security_ok": True})
    assert approved == False
    print("Test 2 PASSED: Score 4 rejected")
    
    # Test 3: Security issue = always reject
    approved, reason = calculate_approval({"score": 10, "security_ok": False})
    assert approved == False
    print("Test 3 PASSED: Security issue rejected")
    
    # Test 4: Medium score with compliance
    approved, reason = calculate_approval({
        "score": 7, 
        "security_ok": True, 
        "project_compliance": True,
        "issues": ["Minor issue"]
    })
    assert approved == True
    print("Test 4 PASSED: Score 7 with compliance approved")
    
    print("All approval tests PASSED!\n")

def test_load_rules():
    """
    Test loading project rules.

    Depends on: .github/swarm_rules.md (Real Project File)
    """
    print("=== LOAD RULES TESTS ===")

    # Pre-check: Verify rules file exists
    rules_path = ".github/swarm_rules.md"
    if not os.path.exists(rules_path):
        print(f"SKIPPING: Real rules file not found at {rules_path}")
        return

    # Test 1: Load real rules file
    content = load_rules()
    assert "HiveMind Global Directives" in content, "Real rules file missing expected header"
    assert "Real Data Only" in content, "Real rules file missing 'Real Data Only' rule"
    print("Test 1 PASSED: Real rules file loaded successfully")

    # Test 2: File missing
    content = load_rules("non_existent_rules.md")
    assert "No project rules found" in content
    print("Test 2 PASSED: Missing file handled gracefully")

    print("All load_rules tests PASSED!\n")

def test_schema_validation():
    print("=== SCHEMA VALIDATION TESTS ===")

    # Check if pydantic is available
    try:
        from pydantic import BaseModel, Field
        from typing import List
    except ImportError:
        print("Skipping schema validation tests: pydantic not found")
        return

    class TestSchema(BaseModel):
        name: str
        age: int
        tags: List[str] = Field(default_factory=list)

    # Test 1: Valid schema
    data = '{"name": "Alice", "age": 30, "tags": ["test"]}'
    result = parse_json_response(data, schema=TestSchema)
    assert result['name'] == "Alice"
    assert result['age'] == 30
    print("Test 1 PASSED: Valid schema")

    # Test 2: Missing fields (should fail Pydantic and return raw dict)
    data = '{"name": "Bob"}' # Missing age
    result = parse_json_response(data, schema=TestSchema)
    # It should return {"name": "Bob"} without age because validation fails
    assert result['name'] == "Bob"
    assert 'age' not in result
    print("Test 2 PASSED: Invalid schema returns raw dict")

    # Test 3: Defaults
    data = '{"name": "Charlie", "age": 25}'
    result = parse_json_response(data, schema=TestSchema)
    assert result['tags'] == [] # Should be filled by default
    print("Test 3 PASSED: Defaults applied")

    # Test 4: Dict schema
    dict_schema = {"name": str, "age": int}
    data = '{"name": "Dave", "age": 40}'
    result = parse_json_response(data, schema=dict_schema)
    assert result['age'] == 40
    print("Test 4 PASSED: Dict schema")

    print("All schema validation tests PASSED!\n")

if __name__ == "__main__":
    try:
        test_json_parsing()
        test_retry_logic()
        test_redaction()
        test_approval_logic()
        test_load_rules()
        test_schema_validation()
        print("=" * 40)
        print("ALL SMOKE TESTS PASSED!")
        print("=" * 40)
    except Exception as e:
        print(f"TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
