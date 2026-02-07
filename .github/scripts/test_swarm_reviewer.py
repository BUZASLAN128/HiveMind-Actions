import sys
import os
import pytest

# Ensure we can import from the same directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from swarm_reviewer import format_review_comment

def test_format_review_comment_approved():
    """Test formatting for an approved review with all details."""
    data = {
        "score": 9,
        "positives": ["Good structure", "Clean code"],
        "issues": [],
        "suggestions": ["Add more comments"],
        "project_compliance": True,
        "security_ok": True
    }
    approved = True
    reason = "Excellent work!"

    comment = format_review_comment(data, approved, reason)

    assert "## HiveMind Code Review" in comment
    assert "**Score:** 9/10" in comment
    assert "**Verdict:** ✅ APPROVED" in comment
    assert "**Project Compliance:** ✅" in comment
    assert "**Security:** ✅" in comment
    assert "> Excellent work!" in comment
    assert "- Good structure" in comment
    assert "- Clean code" in comment
    assert "- No issues detected." in comment
    assert "- Add more comments" in comment

def test_format_review_comment_rejected():
    """Test formatting for a rejected review due to low score."""
    data = {
        "score": 4,
        "positives": [],
        "issues": ["Bug in logic", "Bad variable names"],
        "suggestions": [],
        "project_compliance": False,
        "security_ok": True
    }
    approved = False
    reason = "Too many issues."

    comment = format_review_comment(data, approved, reason)

    assert "**Score:** 4/10" in comment
    assert "**Verdict:** ❌ CHANGES REQUESTED" in comment
    assert "**Project Compliance:** ❌" in comment
    assert "> Too many issues." in comment
    assert "- Bug in logic" in comment
    assert "- Bad variable names" in comment
    assert "- No specific positives mentioned." in comment

def test_format_review_comment_security_issue():
    """Test formatting when security issues are present."""
    data = {
        "score": 0,
        "security_ok": False,
        "issues": ["Hardcoded password"],
    }
    approved = False
    reason = "Security check failed."

    comment = format_review_comment(data, approved, reason)

    assert "**Security:** ⚠️ ATTENTION NEEDED" in comment
    assert "**Verdict:** ❌ CHANGES REQUESTED" in comment
    assert "> Security check failed." in comment

def test_format_review_comment_empty_lists():
    """Test formatting with empty lists for feedback sections."""
    data = {
        "score": 8,
        "positives": [],
        "issues": [],
        "suggestions": [],
        "project_compliance": True,
        "security_ok": True
    }
    approved = True
    reason = "LGTM"

    comment = format_review_comment(data, approved, reason)

    assert "- No specific positives mentioned." in comment
    assert "- No issues detected." in comment
    assert "- No additional suggestions." in comment

def test_format_review_comment_missing_keys():
    """Test formatting when optional keys are missing."""
    data = {} # Missing score, lists, flags
    approved = False
    reason = "Incomplete data"

    comment = format_review_comment(data, approved, reason)

    assert "**Score:** N/A/10" in comment
    # Default behavior for missing keys implies failure/warning
    assert "**Project Compliance:** ❌" in comment
    assert "**Security:** ⚠️ ATTENTION NEEDED" in comment
    assert "- No specific positives mentioned." in comment
